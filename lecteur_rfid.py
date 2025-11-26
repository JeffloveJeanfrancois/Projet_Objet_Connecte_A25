from pirc522 import RFID
import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt
import time
import csv
import os
import json
import sys
from typing import Dict
from carte_autorise import GestionAcces



class LecteurRFID:

    def __init__(self, 
                 broche_buzzer=33, 
                 delai_lecture=2, 
                 nom_fichier = "journal_rfid.csv",
                 led_rouge = 38,
                 led_verte = 40,
                 broker = "192.168.40.122",
                 port = 1883,
                 sujet_log = "LecteurRFID/log",
                 fichier_cartes = "cartes_autorisees.json",
                 fichier_cartes_csv = "cartes_autorisees.csv"
              ):
      
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
        self.fichier_cartes = fichier_cartes
        self.fichier_cartes_csv = fichier_cartes_csv
        self.cartes_autorisees = self._charger_cartes_autorisees()
        self.gestion_acces = GestionAcces(self.fichier_cartes_csv)


        # Mémorise la dernière carte lue 
        self.derniere_carte = None
        self.dernier_temps = 0

        self.broker = broker
        self.port = 1883
        self.sujet_log = sujet_log

        self.client = mqtt.Client()
        self.client.connect(self.broker, self.port, 60)

        # Création du fichier CSV s'il n'existe pas encore
        if not os.path.exists(nom_fichier):
            with open(nom_fichier, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Date/Heure", "Type de carte", "UID", "Nom", "Statut"])
        self.gestion_acces.creer_fichier_si_absent()

        print("Lecteur RFID prêt. Approchez une carte !")

    def _charger_cartes_autorisees(self) -> Dict:
        if not os.path.exists(self.fichier_cartes):
            print(f"Le fichier {self.fichier_cartes} n'existe pas")
            sys.exit(1)
        
        try:
            with open(self.fichier_cartes, 'r') as fichier:
                data = json.load(fichier)
                resultat = {}
                for carte in data.get('cartes', []):
                    uid = carte.get('uid')
                    if uid:
                        resultat[carte['uid']] = {
                            'nom': carte.get('nom', 'Inconnu'),
                            'actif': carte.get('actif', False)
                        }
                return resultat
        except Exception as exception:
            print(f"Erreur lors du chargement des cartes: {exception}")
            return {}

    # Fonction pour faire biper le buzzer ---
    def bip(self, duree=0.3):
        GPIO.output(self.buzzer, True)
        time.sleep(duree)
        GPIO.output(self.buzzer, False)

    def gestion_led(self, duree=0.3):
        GPIO.output(self.led_verte, GPIO.HIGH)
        GPIO.output(self.led_rouge, GPIO.HIGH)
        time.sleep(duree)
        GPIO.output(self.led_verte, GPIO.LOW)
        GPIO.output(self.led_rouge, GPIO.LOW)

    # Fonction pour afficher les infos de la carte 
    def afficher_carte(self, type_carte, uid):
        #uid_hex = ' '.join(f'{octet:02X}' for octet in uid)
        print("\n####### Nouvelle carte détectée #######")
        print(f"Type : {type_carte}")
        print(f"UID  : {uid}")
        print("****************************************")

    def _verifier_carte(self, uid):
        if uid in self.cartes_autorisees:
            carte_info = self.cartes_autorisees[uid]
            if carte_info['actif']:
                return True, carte_info['nom'], "Accepté"
            else:
                return False, carte_info['nom'], "Carte désactivée"
        else:
            return False, "Non renseigné", "Refusé - Carte non autorisée"
        
    # Fonction pour enregistrer dans le CSV 
    def enregistrer(self, type_carte, uid, nom, statut):
        date = time.strftime("%Y-%m-%d %H:%M:%S")
        uid_str = "-".join(str(octet) for octet in uid)
        
        with open(self.nom_fichier, 'a', newline='', encoding='utf-8') as fichier_csv:
            writer = csv.writer(fichier_csv)
            writer.writerow([date, type_carte, uid_str, nom, statut])

    def publier_info_carte(self, date, type_carte, uid):
        uid_str = "-".join(str(octet) for octet in uid)
        info_carte = json.dumps({
            "date_heure": date,
            "type_carte": type_carte,
            "uid": uid_str
        })
        sujet_carte = f"{self.sujet_log}/{int(time.time())}"
        self.client.publish(sujet_carte, info_carte, qos=1, retain=False)
        self.client.loop()
        print(f"info carte envoyé sur {self.sujet_log} : {info_carte}")
       
    # Boucle principale 
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

                # Vérification de la carte avec json
                uid_string = "-".join(str(octet) for octet in uid)
                #est_autorisee, nom, statut = self._verifier_carte(uid_string) 

                #verification avec fichier csv 
                est_autorisee, nom, statut = self.gestion_acces.verifier_carte(uid_string)

                
                # Affichage + bip + enregistrement
                date = time.strftime("%Y-%m-%d %H:%M:%S")
                self.afficher_carte(type_carte, uid)
                print(f"Nom: {nom}")
                print(f"Statut: {statut}")
                
                # Feedback visuel et sonore selon le statut
                if est_autorisee:
                    GPIO.output(self.led_verte, GPIO.HIGH)
                    self.bip(0.2)  # Bip court pour accès autorisé
                    GPIO.output(self.led_verte, GPIO.LOW)
                else:
                    GPIO.output(self.led_rouge, GPIO.HIGH)
                    self.bip(0.8)  # Bip long pour accès refusé
                    GPIO.output(self.led_rouge, GPIO.LOW)
                
                self.publier_info_carte(date, type_carte, uid)
                self.enregistrer(type_carte, uid, nom, statut)


                # Mémorisation de la dernière carte
                self.derniere_carte = uid
                self.dernier_temps = temps_actuel

        except KeyboardInterrupt:
            print("\n Arrêt du programme par l’utilisateur.")
        finally:
            try:
                GPIO.cleanup()
            except RuntimeWarning:
                pass
            self.rfid.cleanup()
            print(" Nettoyage terminé.")



