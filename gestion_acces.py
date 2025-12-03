import time
import RPi.GPIO as GPIO
import threading


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
    # Lancer LED + bip simultanément
        thread_led = threading.Thread(target=self._allumer_led, args=(self.led_verte, 2))
        thread_bip = threading.Thread(target=self._bip, args=(0.2,))

        thread_led.start()
        thread_bip.start()

        # Attendre la fin des threads AVANT d'afficher
        thread_led.join()
        thread_bip.join()

        # Affichage sur l'écran
        if self.ecran:
            self.ecran.afficher(
                ligne1="ACCES ACCEPTE",
                ligne2=f"Bienvenue {nom}"[:16],
                duree=4
            )



    def carte_refusee(self):
        thread_led = threading.Thread(target=self._allumer_led, args=(self.led_rouge, 2))
        thread_bip = threading.Thread(target=self._bip, args=(0.8,))

        thread_led.start()
        thread_bip.start()

        thread_led.join()
        thread_bip.join()

        if self.ecran:
            self.ecran.afficher(
                ligne1="ACCES REFUSE",
                ligne2="Carte Invalide",
                duree=4
            )
