from pirc522 import RFID
from typing import Optional, List

class CarteConfiguration:

    def __init__(self, rdr: RFID | None = None, CLE=None):
        self.rdr = rdr
        self.CLE = CLE if CLE is not None else [0xFF] * 6

        # ensemble de cle possible
        self.COMMON_KEYS = [
            [0xFF]*6,
            [0xA0]*6,
            [0x00]*6,
            [0xD3, 0xF7, 0xD3, 0xF7, 0xD3, 0xF7],
            [0xA1]*6,
            [0xB0]*6,
        ]

    def est_bloc_remorque(self, numero_bloc: int) -> bool:
        return (numero_bloc + 1) % 4 == 0

    def authentifier(self, uid, bloc: int) -> bool:
        self.rdr.select_tag(uid)  

        # Essai clé principale
        if self.rdr.card_auth(self.rdr.auth_a, bloc, self.CLE, uid) == 0:
            return True

        # Essai toutes les clés communes
        for key in self.COMMON_KEYS:
            if self.rdr.card_auth(self.rdr.auth_a, bloc, key, uid) == 0:
                self.CLE = key
                return True

        return False


    def lire_bloc(self, uid, bloc: int) -> Optional[List[int]]:
        if self.est_bloc_remorque(bloc):
            print(f"[INFO] Bloc {bloc} est un trailer — lecture interdite.")
            return None

        if not self.authentifier(uid, bloc):
            print(f"[ERREUR] Auth échouée bloc {bloc}")
            return None

        status, data = self.rdr.read(bloc)
        self.rdr.stop_crypto()

        if status != 0 or data is None:
            print(f"[ERREUR] Lecture bloc {bloc} impossible")
            return None

        texte = ''.join(chr(x) if 32 <= x <= 126 else '.' for x in data)
        hexdata = " ".join(f"{x:02X}" for x in data)
        print(f"[Bloc {bloc}] {hexdata} | {texte}")

        return data


    def ecrire_bloc(self, uid, bloc: int, texte: str) -> bool:
        if self.est_bloc_remorque(bloc):
            print(f"[ERREUR] Bloc trailer {bloc}, écriture interdite.")
            return False

        # Authentification avec toutes les clés 
        if not self.authentifier(uid, bloc):
            print(f"[ERREUR] Auth échouée bloc {bloc}")
            return False

        # Préparer les 16 octets
        data = list(texte.encode("ascii")[:16])
        data += [0] * (16 - len(data))

        # Écriture du bloc
        status = self.rdr.write(bloc, data)
        self.rdr.stop_crypto()

        if status != 0:
            print(f"[ERREUR] Écriture échouée bloc {bloc}")
            return False

        print(f"[INFO] Bloc {bloc} écrit avec succès : {texte}")

        # Relire immédiatement pour afficher le contenu réel
        #contenu_lu = self.lire_bloc(uid, bloc)
        #if contenu_lu:
        #    texte_lu = ''.join(chr(x) if 32 <= x <= 126 else '.' for x in contenu_lu)
        print(f"[INFO] Contenu réel du bloc {bloc} après écriture : {texte}")

        return True


    def lire_blocs(self, uid, blocs: List[int]) -> str:
        texte_total = ""
        for bloc in blocs:
            if not self.est_bloc_remorque(bloc):
                data = self.lire_bloc(uid, bloc)
                if data:
                    texte_total += ''.join(chr(x) if 32 <= x <= 126 else '.' for x in data)
        return texte_total
    
