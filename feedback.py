import time
import RPi.GPIO as GPIO


class FeedbackGPIO:
    """Encapsule l'accès GPIO pour LED et buzzer."""

    def __init__(self, led_verte: int, led_rouge: int, buzzer: int):
        self.led_verte = led_verte
        self.led_rouge = led_rouge
        self.buzzer = buzzer

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        for pin in (self.led_verte, self.led_rouge, self.buzzer):
            GPIO.setup(pin, GPIO.OUT)

    def _allumer_led(self, led: int, duree: float):
        GPIO.output(led, GPIO.HIGH)
        time.sleep(duree)
        GPIO.output(led, GPIO.LOW)

    def vert(self, duree: float = 2.0):
        self._allumer_led(self.led_verte, duree)

    def rouge(self, duree: float = 2.0):
        self._allumer_led(self.led_rouge, duree)

    def bip(self, duree: float = 0.3):
        GPIO.output(self.buzzer, True)
        time.sleep(duree)
        GPIO.output(self.buzzer, False)

    def cleanup(self):
        GPIO.cleanup()
