from pirc522 import RFID
from card_utils import string_to_block_list, block_list_to_string

# ensemble de cle possible
COMMON_KEYS = [
    [0xFF]*6,
    [0xA0]*6,
    [0x00]*6,
    [0xD3, 0xF7, 0xD3, 0xF7, 0xD3, 0xF7],
    [0xA1]*6,
    [0xB0]*6,
]

class LecteurRFID:
    def __init__(self, rdr: RFID, CLE=None):
        self.rdr = rdr
        self.CLE = CLE if CLE is not None else [0xFF] * 6

    def est_bloc_remorque(self, block_number: int) -> bool:
        """Vérifie si le numéro de bloc passé correspond à un bloc trailer (remorque)"""
        return (block_number + 1) % 4 == 0

    def authentifier(self, uid: list[int], block: int) -> bool:
        """Authentification avec toutes les clés"""
        self.rdr.select_tag(uid)

        # Essai clé principale
        if self.rdr.card_auth(self.rdr.auth_a, block, self.CLE, uid) == 0:
            return True

        # Essai toutes les clés communes
        for key in COMMON_KEYS:
            if self.rdr.card_auth(self.rdr.auth_a, block, key, uid) == 0:
                self.CLE = key
                return True

        return False

    def ecrire_bloc(self, uid: list[int], block: int, block_data: list[int]) -> bool:
        """
        Écrit dans un bloc spécifique de la carte RFID.

        - Les blocs trailer sont interdits.
        - Retourne True si une erreur s'est produite, False sinon.
        """
        if self.est_bloc_remorque(block):
            print(f"[ERREUR] Bloc trailer {block}, ecriture interdite.")
            return True
 
        if not self.authentifier(uid, block):
            print(f"[ERREUR] Auth echouee pour le bloc {block}")
            return True

        error = self.rdr.write(block, block_data)
        self.rdr.stop_crypto()

        if error:
            print(f"[ERREUR] Ecriture echouee bloc {block}")
            return True

        return False

    def lire_bloc(self, uid: list[int], block: int) -> tuple[bool, list[int]]:
        """
        Lit un bloc sur la carte RFID.

        Retourne un tuple : (error: bool, data: List[int])
        - error : True si une erreur s'est produite, False sinon
        - data : liste de 16 octets si lecture réussie, liste vide en cas d'erreur
        """
        if self.est_bloc_remorque(block):
            print(f"[INFO] Bloc {block} est un trailer — lecture interdite.")
            return True, []

        if not self.authentifier(uid, block):
            print(f"[ERREUR] Auth echouee pour le bloc {block}")
            return True, []

        error, data = self.rdr.read(block)
        self.rdr.stop_crypto()

        if error or data is None or len(data) != 16:
            print(f"[ERREUR] Lecture bloc {block} impossible")
            return True, []

        return False, data

    def lire_blocs(self, uid: list[int], blocks: list[int]) -> str:
        """
        Lit plusieurs blocs sur la carte RFID et retourne leur contenu formaté.

        Pour chaque bloc :
        - Indique le numéro du bloc
        - Affiche le texte lu (octets non imprimables remplacés par '.')
        - Les blocs trailer ou les blocs non lus sont ignorés
        """
        result_lines = []

        for block in blocks:
            if self.est_bloc_remorque(block):
                continue
            
            error, data = self.lire_bloc(uid, block)

            if error:
                print(f"[AVERTISSEMENT] Lecture du bloc {block} a echouee, bloc ignore.")
                continue

            text = block_list_to_string(data)

            # Ajoute une ligne formatée pour ce bloc
            result_lines.append(f"Bloc {block}: {text}")
            
        return '\n'.join(result_lines)
