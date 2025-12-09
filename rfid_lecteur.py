from pirc522 import RFID
from card_utils import string_to_block_list, block_list_to_string
from typing import Optional

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
    BLOCK_SIZE = 16

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

    def ecrire_bloc(self, block: int, block_data: list[int], uid: Optional[list[int]] = None, auto_auth: bool = True) -> bool:
        """
        Écrit dans un bloc spécifique de la carte RFID.
        - Les blocs trailer sont interdits.
        Args:
            block: Numéro du bloc à lire.
            block_data: Liste de 16 octets à écrire dans le bloc.
            uid: UID de la carte (requis si auto_auth=True, peut être None sinon).
            auto_auth: 
                - True: authentifie automatiquement et stop_crypto() après.
                - False: laisse l'appelant gérer l'authentification.
        Returns:
            bool: True si une erreur s'est produite, False sinon
        """
        if self.est_bloc_remorque(block):
            print(f"[ERREUR] Bloc trailer {block}, ecriture interdite.")
            return True
 
        if auto_auth:
            if uid is None:
                print(f"[ERREUR] L'UID est requis lorsque auto_auth est vrai.")
                return True
            if not self.authentifier(uid, block):
                print(f"[ERREUR] Auth echouee pour le bloc {block}")
                return True

        try:
            error = self.rdr.write(block, block_data)
            if error:
                print(f"[ERREUR] Ecriture echouee bloc {block}")
                return True
            
            return False
        finally:
            if auto_auth:
                self.rdr.stop_crypto()

    def lire_bloc(self, block: int, uid: Optional[list[int]] = None, auto_auth: bool = True) -> tuple[bool, list[int]]:
        """
        Lit un bloc sur la carte RFID.
        - Les blocs trailer sont interdits.
        Args:
            block: Numéro du bloc à lire.
            uid: UID de la carte (requis si auto_auth=True, peut être None sinon).
            auto_auth: 
                - True: authentifie automatiquement et stop_crypto() après.
                - False: laisse l'appelant gérer l'authentification.
        Returns:
            tuple: [bool, list[int]]
                - error: True si une erreur s'est produite, False sinon
                - data: liste de 16 octets si lecture réussie, liste vide en cas d'erreur
        """
        if self.est_bloc_remorque(block):
            print(f"[INFO] Bloc {block} est un trailer — lecture interdite.")
            return True, []

        if auto_auth:
            if uid is None:
                print(f"[ERREUR] L'UID est requis lorsque auto_auth est vrai.")
                return True, []
            if not self.authentifier(uid, block):
                print(f"[ERREUR] Auth echouee pour le bloc {block}")
                return True, []

        try:
            error, data = self.rdr.read(block)
            if error or data is None or len(data) != self.BLOCK_SIZE:
                print(f"[ERREUR] Lecture bloc {block} impossible")
                return True, []
            
            return False, data
        finally:
            if auto_auth:
                self.rdr.stop_crypto()

    def lire_blocs(self, blocks: list[int], uid: list[int], ) -> str:
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
            
            error, data = self.lire_bloc(block, uid)

            if error:
                print(f"[AVERTISSEMENT] Lecture du bloc {block} a echouee, bloc ignore.")
                continue

            text = block_list_to_string(data)

            # Ajoute une ligne formatée pour ce bloc
            result_lines.append(f"Bloc {block}: {text}")
            
        return '\n'.join(result_lines)
