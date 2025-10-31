# --- Importation des modules nécessaires ---
from pirc522 import RFID
import RPi.GPIO as GPIO
import time
import csv
import os


class LecteurRFID:

    def __init__(self, 
                 broche_buzzer=33, 
                 delai_lecture=2, 
                 nom_fichier="journal_rfid.csv",
                 led_rouge=38,
                 led_verte=40):
        # --- Configuration de base ---
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(broche_buzzer, GPIO.OUT)
        GPIO.setup(led_rouge, GPIO.OUT)
        GPIO.setup(led_verte, GPIO.OUT)

        self.rfid = RFID(pin_irq=None)
        self.buzzer = broche_buzzer
        self.led_rouge = led_rouge
        self.led_verte = led_verte
        self.delai_lecture = delai_lecture
        self.nom_fichier = nom_fichier

        # Mémorise la dernière carte lue pour éviter les doublons
        self.derniere_carte = None
        self.dernier_temps = 0

        # Création du fichier CSV avec en-tête s’il n’existe pas encore
        if not os.path.exists(nom_fichier):
            with open(nom_fichier, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Date/Heure", "Type de carte", "UID"])

        print("Lecteur RFID prêt. Approchez une carte !")

    # --- Fonction pour faire biper le buzzer ---
    def bip(self, duree=0.3):
        GPIO.output(self.buzzer, True)
        GPIO.output(self.led_verte, GPIO.HIGH)
        GPIO.output(self.led_rouge, GPIO.HIGH)
        time.sleep(duree)
        GPIO.output(self.buzzer, False)

    # --- Fonction pour afficher les infos de la carte ---
    def afficher_carte(self, type_carte, uid):
        #uid_hex = ' '.join(f'{octet:02X}' for octet in uid)
        print("\n####### Nouvelle carte détectée #######")
        print(f"Type : {type_carte}")
        print(f"UID  : {uid}")
        print("****************************************")

    # --- Fonction pour enregistrer dans le CSV ---
    def enregistrer(self, type_carte, uid):
        date = time.strftime("%Y-%m-%d %H:%M:%S")
        #uid_hex = ' '.join(f'{octet:02X}' for octet in uid)
        uid_str = "-".join(str(octet) for octet in uid)
        with open(self.nom_fichier, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([date, type_carte, uid_str])

    # --- Boucle principale ---
    def lancer(self):
        print(" En attente d’une carte...")

        try:

            while True:
                #self.rfid.wait_for_tag()
                (erreur, type_carte) = self.rfid.request()
                if erreur:
                    time.sleep(0.1)
                    continue

                (erreur, uid) = self.rfid.anticoll()
                if erreur:
                    continue

                temps_actuel = time.time()

                # Vérifie si la même carte a été lue trop récemment
                if self.derniere_carte == uid and (temps_actuel - self.dernier_temps) < self.delai_lecture:
                    print("Cette carte a déjà été utilisée il y a moins de 5 secondes, veuillez patienter un peu...")
                    time.sleep(0.5)
                    continue

                # Affichage + bip + enregistrement
                self.afficher_carte(type_carte, uid)
                self.bip()
                GPIO.output(self.led_verte, GPIO.LOW)
                GPIO.output(self.led_rouge, GPIO.LOW)
                self.enregistrer(type_carte, uid)


                # Mémorisation de la dernière carte
                self.derniere_carte = uid
                self.dernier_temps = temps_actuel

        except KeyboardInterrupt:
            print("\n Arrêt du programme par l’utilisateur.")
        finally:
            GPIO.cleanup()
            self.rfid.cleanup()
            print(" Nettoyage terminé.")


