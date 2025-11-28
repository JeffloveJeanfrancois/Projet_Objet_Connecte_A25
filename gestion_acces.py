# Fichier: gestion_acces.py

import time
import RPi.GPIO as GPIO

class GestionAcces:

    def __init__(self, led_verte=40, led_rouge=38, buzzer=33, ecran=None): # <--- AJOUT DE ecran
        # La configuration GPIO est déléguée à LecteurRFID
        self.led_verte = led_verte
        self.led_rouge = led_rouge
        self.buzzer = buzzer
        self.ecran = ecran # <--- STOCKAGE DE L'INSTANCE ÉCRAN

    # ---------- Signaux physiques ----------
    def _allumer_led(self, led, duree):
        GPIO.output(led, GPIO.HIGH)
        time.sleep(duree)
        GPIO.output(led, GPIO.LOW)

    def _bip(self, duree):
        GPIO.output(self.buzzer, True)
        time.sleep(duree)
        GPIO.output(self.buzzer, False)

    # ---------- Scénarios utilisateur ----------
    def carte_acceptee(self, nom=""):
        # Affichage du message dans la console (géré par verification.py)

        self._allumer_led(self.led_verte, 2)   # LED verte 2s
        self._bip(0.2)                         # Bip court 0.2s
        
        if self.ecran: # <--- GESTION DE L'AFFICHAGE (maintenant ici)
            self.ecran.afficher(
                ligne1="ACCES ACCEPTE", 
                ligne2=f"Bienvenue {nom}"[:16], # Affiche les 16 premiers caractères
                duree=4
            )

    def carte_refusee(self):
        # Affichage du message dans la console (géré par verification.py)
        
        self._allumer_led(self.led_rouge, 2)   # LED rouge 2s
        self._bip(0.8)                         # Bip long 0.8s
        
        if self.ecran: # <--- GESTION DE L'AFFICHAGE (maintenant ici)
            self.ecran.afficher(
                ligne1="ACCES REFUSE", 
                ligne2="Carte Invalide", 
                duree=4
            )