# Fichier: affichage_qapass.py

from time import sleep
from RPLCD.i2c import CharLCD
import sys # Ajout pour un exit propre si l'initialisation échoue

class AffichageQapass:

    def __init__(self, i2c_addr=0x27, port=1, cols=16, rows=2):
        
        # 1. Stocker les dimensions ici
        self.cols = cols 
        self.rows = rows
        
        try:
            # Initialisation de l'écran LCD I2C
            self.lcd = CharLCD(
                i2c_expander='PCF8574', 
                address=i2c_addr, 
                port=port, 
                cols=cols, 
                rows=rows,
                charmap='A00'
            )
            self.lcd.clear()
            print(f"Écran QAPASS initialisé (I2C: 0x{i2c_addr:x})")
        except Exception as e:
            print(f"⚠️ Erreur lors de l'initialisation de l'écran LCD : {e}. Affichage désactivé.")
            self.lcd = None 
            # Note: Le programme continue de tourner grâce au 'return' dans afficher/accueil

    # Dans la classe AffichageQapass

    def afficher(self, ligne1="", ligne2="", duree=0):
        if self.lcd is None:
            return

        # On efface et on écrit le message
        self.lcd.clear()
        
        self.lcd.cursor_pos = (0, 0)
        self.lcd.write_string(ligne1[:self.cols].ljust(self.cols)) # Sécurité sur la longueur
        
        if self.rows > 1:
            self.lcd.cursor_pos = (1, 0)
            self.lcd.write_string(ligne2[:self.cols].ljust(self.cols))
        
        # Gestion du temps d'affichage
        if duree > 0:
            sleep(duree) # Ce sleep ne bloquera que le thread de l'écran, pas le reste
            self.accueil() # Retour au message par défaut après le délai

    def accueil(self):
        # Assurez-vous d'appeler afficher() sans argument duree pour ne pas boucler
        self.afficher(ligne1="APPROCHEZ VOTRE", ligne2="CARTE RFID")
        
    def nettoyer(self):
        if self.lcd:
            self.lcd.clear()