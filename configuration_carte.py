import sys, os
from mfrc522 import MFRC522

class CarteConfiguration:

    def __init__(self, CLE=[0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]):

        self.mfrc = MFRC522()
        self.CLE = CLE
    
    def est_bloc_remorque(self, numero_bloc):
        return (numero_bloc + 1) % 4 == 0
    
    def auth_silencieuse(self, bloc, clé, uid):
        stdout_orig = sys.stdout
        sys.stdout = open(os.devnull, 'w')
        resultat = self.mfrc.MFRC522_Auth(self.mfrc.PICC_AUTHENT1A, bloc, clé, uid)
        sys.stdout.close()
        sys.stdout = stdout_orig
        return resultat


    def lire_bloc(self, uid, numero_bloc):
        if self.auth_silencieuse(numero_bloc, self.CLE, uid) != self.mfrc.MI_OK:
            print(f"[ERREUR] Impossible de lire le bloc {numero_bloc}. Vérifie la clé ou le bloc.")
            return None
    

        
        data = self.mfrc.MFRC522_Read(numero_bloc)
        self.mfrc.MFRC522_StopCrypto1()
        
        if data is None:
            print("Lecture impossible")
            return None

        try:
            return bytes(data).decode("utf-8", errors="ignore")
        except:
            return "".join(chr(x) for x in data if 32 <= x <= 126)
        


    def lire_blocs(self, uid, blocs):

        texte_total = ''

        for bloc in blocs:
            if not self.est_bloc_remorque(bloc):
                print(f"Lecture du bloc {bloc}")
                mot = self.lire_bloc(uid, bloc)
                if mot:
                    texte_total += mot
        return texte_total

    
    
    def ecrire_bloc(self, uid, numero_bloc, texte):

        if self.est_bloc_remorque(numero_bloc):
            raise ValueError(f"Impossible d’écrire dans un bloc remorque : {numero_bloc}")

        # Authentification
        if self.auth_silencieuse(
            numero_bloc,
            self.CLE,
            uid
        ) != self.mfrc.MI_OK:
            print(f"[ERREUR] Impossible d’écrire sur le bloc {numero_bloc}. Vérifie la clé ou le bloc.")
            return False

        data = texte.encode("utf-8")[:16]
        data = data.ljust(16, b'\x00')
        succes = self.mfrc.MFRC522_Write(numero_bloc, list(data)) == self.mfrc.MI_OK
        self.mfrc.MFRC522_StopCrypto1()  

        if not succes:
            print(f"[ERREUR] Écriture échouée bloc {numero_bloc}")
        return succes
 