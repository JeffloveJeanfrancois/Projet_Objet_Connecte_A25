import sys, os
from mfrc522 import MFRC522

class CardReader:
    def __init__(self, CLE=None):
        self.mfrc = MFRC522()
        self.CLE = CLE if CLE is not None else [0xFF] * 6
    
    def est_bloc_remorque(self, numero_bloc):
        return (numero_bloc + 1) % 4 == 0
    
    def remorque_pour_bloc(self, numero_bloc):
        secteur = numero_bloc // 4
        return secteur * 4 + 3
    
    def auth_silencieuse(self, bloc, cle, uid):
        stdout_orig = sys.stdout
        try:
            sys.stdout = open(os.devnull, 'w')
            return self.mfrc.MFRC522_Auth(self.mfrc.PICC_AUTHENT1A, bloc, cle, uid)
        finally:
            sys.stdout.close()
            sys.stdout = stdout_orig

    def lire_bloc(self, uid, numero_bloc):
        if self.auth_silencieuse(numero_bloc, self.CLE, uid) != self.mfrc.MI_OK:
            print(f"[ERREUR] Impossible de lire le bloc {numero_bloc}. Verifie la cle ou le bloc.")
            return None
        
        data = self.mfrc.MFRC522_Read(numero_bloc)
        self.mfrc.MFRC522_StopCrypto1()
        
        if data is None:
            print("Lecture impossible")
            return None

        return bytes(data)

    def lire_blocs(self, uid, blocs):
        resultat = b''
        for bloc in blocs:
            if not self.est_bloc_remorque(bloc):
                print(f"Lecture du bloc {bloc}")
                data = self.lire_bloc(uid, bloc)
                if data:
                    resultat += data
        return resultat
    
    def ecrire_bloc(self, uid, numero_bloc, data: bytes) -> bool:
        if self.est_bloc_remorque(numero_bloc):
            raise ValueError(f"Impossible d'ecrire dans un bloc remorque : {numero_bloc}")

        # Authentification
        if self.auth_silencieuse(numero_bloc, self.CLE, uid) != self.mfrc.MI_OK:
            print(f"[ERREUR] Impossible d'ecrire sur le bloc {numero_bloc}. Verifie la cle ou le bloc.")
            return False

        # truncate/pad to 16 bytes
        if len(data) > 16:
            data = data[:16]
        data = data.ljust(16, b'\x00')

        succes = self.mfrc.MFRC522_Write(numero_bloc, list(data)) == self.mfrc.MI_OK
        self.mfrc.MFRC522_StopCrypto1()  

        if not succes:
            print(f"[ERREUR] ecriture echouee bloc {numero_bloc}")
        return succes
    
    # ---- Convenience methods ----
    def lire_texte_bloc(self, uid, numero_bloc):
        """Read a block and return decoded UTF-8 string (ignores invalid chars)."""
        data = self.lire_bloc(uid, numero_bloc)
        if data is None:
            return None
        return data.split(b'\x00', 1)[0].decode('utf-8', errors='ignore')

    def ecrire_texte_bloc(self, uid, numero_bloc, texte: str):
        """Write a UTF-8 string to a block."""
        return self.ecrire_bloc(uid, numero_bloc, texte.encode('utf-8'))
