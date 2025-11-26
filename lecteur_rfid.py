import time
import csv
import os
import json
import RPi.GPIO as GPIO
from pirc522 import RFID
import paho.mqtt.client as mqtt

from gestion_acces import GestionAcces           # LEDs + buzzer + messages
from verification import identifier_carte      # vérifie si la carte est autorisée


class LecteurRFID:

    def __init__(self,
                 broche_buzzer=33,
                 delai_lecture=2,
                 nom_fichier="journal_rfid.csv",
                 led_rouge=38,
                 led_verte=40,
                 broker="192.168.40.122",
                 port=1883,
                 sujet_log="LecteurRFID/log"
                 ):

        # Configuration GPIO
        GPIO.setmode(GPIO.BOARD)

        self.rfid = RFID(pin_irq=None)
        self.buzzer = broche_buzzer
        self.led_rouge = led_rouge
        self.led_verte = led_verte

        # Gestion accès (LED + buzzer + console)
        self.acces = GestionAcces(
            led_verte=self.led_verte,
            led_rouge=self.led_rouge,
            buzzer=self.buzzer
        )

        self.delai_lecture = delai_lecture
        self.nom_fichier = nom_fichier

        self.derniere_carte = None
        self.dernier_temps = 0

        # MQTT
        self.broker = broker
        self.port = port
        self.sujet_log = sujet_log

        self.client = mqtt.Client()
        self.client.connect(self.broker, self.port, 60)

        # Création du fichier CSV si inexistant
        if not os.path.exists(nom_fichier):
            with open(nom_fichier, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Date/Heure", "UID", "Accès"])

        print("Lecteur RFID prêt. Approchez une carte !")

    # ---------------------------------------------------
    # Enregistrement local CSV
    # ---------------------------------------------------
    def enregistrer(self, uid, acces):
        date = time.strftime("%Y-%m-%d %H:%M:%S")
        uid_str = "-".join(str(octet) for octet in uid)

        with open(self.nom_fichier, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([date, uid_str, acces])

    # ---------------------------------------------------
    # Publication MQTT
    # ---------------------------------------------------
    def publier_info_carte(self, uid, acces):
        info_carte = json.dumps({
            "date_heure": time.strftime("%Y-%m-%d %H:%M:%S"),
            "uid": "-".join(str(o) for o in uid),
            "acces": acces
        })

        sujet = f"{self.sujet_log}/{int(time.time())}"
        self.client.publish(sujet, info_carte, qos=1, retain=False)
        self.client.loop()

        print(f"Info carte envoyée sur MQTT : {info_carte}")

    # ---------------------------------------------------
    # Boucle principale
    # ---------------------------------------------------
    def lancer(self):
        print("En attente d’une carte...")

        try:
            while True:

                (erreur, type_carte) = self.rfid.request()
                if erreur:
                    time.sleep(0.05)
                    continue

                (erreur, uid) = self.rfid.anticoll()
                if erreur:
                    continue

                temps_actuel = time.time()

                # Anti-spam : carte lue trop vite
                if self.derniere_carte == uid and (temps_actuel - self.dernier_temps) < self.delai_lecture:
                    print("Carte déjà utilisée récemment, patientez...")
                    continue

                print("\n===== Carte détectée =====")
                print("UID :", uid)

                # Vérification d’accès
                carte_ok = identifier_carte(uid)

                if carte_ok:
                    self.acces.carte_acceptee()
                    acces = "accepte"
                else:
                    self.acces.carte_refusee()
                    acces = "refuse"

                # Enregistrements
                self.enregistrer(uid, acces)
                self.publier_info_carte(uid, acces)

                # Mémorisation pour éviter les doublons
                self.derniere_carte = uid
                self.dernier_temps = temps_actuel

        except KeyboardInterrupt:
            print("\nArrêt du programme.")

        finally:
            GPIO.cleanup()
            self.rfid.cleanup()
            print("GPIO nettoyé – Fin du programme.")
