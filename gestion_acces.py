import time
import RPi.GPIO as GPIO

class GestionAcces:

    def __init__(self, led_verte=40, led_rouge=38, buzzer=33):
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(led_verte, GPIO.OUT)
        GPIO.setup(led_rouge, GPIO.OUT)
        GPIO.setup(buzzer, GPIO.OUT)

        self.led_verte = led_verte
        self.led_rouge = led_rouge
        self.buzzer = buzzer

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
        print(f"Bienvenue {nom}")
        self._allumer_led(self.led_verte, 2)   # LED verte 2s
        self._bip(0.2)                         # Bip court 0.2s

    def carte_refusee(self):
        print("Accès refusé")
        self._allumer_led(self.led_rouge, 2)   # LED rouge 2s
        self._bip(0.8)                         # Bip long 0.8s
