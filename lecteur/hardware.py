import RPi.GPIO as GPIO
import time

class LedBuzzer:

    def __init__(self, buzzer=33, led_rouge=38, led_verte=40):
        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)
        GPIO.setup(buzzer, GPIO.OUT)
        GPIO.setup(led_rouge, GPIO.OUT)
        GPIO.setup(led_verte, GPIO.OUT)

        self.buzzer = buzzer
        self.led_r = led_rouge
        self.led_v = led_verte

    def ok(self):
        GPIO.output(self.led_v, True)
        self._beep(0.2)
        GPIO.output(self.led_v, False)

    def erreur(self):
        GPIO.output(self.led_r, True)
        self._beep(0.8)
        GPIO.output(self.led_r, False)

    def _beep(self, duree):
        GPIO.output(self.buzzer, True)
        time.sleep(duree)
        GPIO.output(self.buzzer, False)
