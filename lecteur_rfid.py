from pirc522 import RFID
import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt
import time
import csv
import os
import json



from gestion_acces import GestionAcces           # LEDs + buzzer + messages
from verification import identifier_carte      # vérifie si la carte est autorisée
from affichage_qapass import AffichageQapass
import sys
from typing import Dict
from card_reader import CardReader
from configuration_carte import CarteConfiguration

from cartes_autorisees import GestionAcces as GestionCartesCSV

class LecteurRFID:

    def __init__(self,
                 broche_buzzer=33,
                 delai_lecture=2,
                 nom_fichier="journal_rfid.csv",
                 led_rouge=38,
                 led_verte=40,
                 broker="10.4.1.164",
                 port=1883,
                 sujet_log="LecteurRFID/log",
                 fichier_cartes="cartes_autorisees.csv",       
                 utiliser_mqtt = True
                 ):

        # Configuration GPIO
        GPIO.setwarnings(False)     
        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)
        GPIO.setup(broche_buzzer, GPIO.OUT)
        GPIO.setup(led_rouge, GPIO.OUT)
        GPIO.setup(led_verte, GPIO.OUT)

        self.rfid = RFID(pin_irq=None)
        self.buzzer = broche_buzzer
        self.led_rouge = led_rouge
        self.led_verte = led_verte

        GPIO.setup(self.led_verte, GPIO.OUT)  # <-- AJOUTEZ CECI
        GPIO.setup(self.led_rouge, GPIO.OUT)  # <-- AJOUTEZ CECI
        GPIO.setup(self.buzzer, GPIO.OUT)     # <-- AJOUTEZ CECI

        self.ecran = AffichageQapass()

        # Gestion accès (LED + buzzer + console)
        self.acces = GestionAcces(
            led_verte=self.led_verte,
            led_rouge=self.led_rouge,
            buzzer=self.buzzer,
            ecran=self.ecran
        )

        self.delai_lecture = delai_lecture
        self.nom_fichier = nom_fichier
        self.fichier_cartes = fichier_cartes
        self.gestion_csv = GestionCartesCSV(nom_fichier=self.fichier_cartes)
        self.mifare = CarteConfiguration(rdr=self.rfid)
        self.questions_admin = self._charger_questions_admin("pass.json")


        # Mémorise la dernière carte lue 
        self.derniere_carte = None
        self.dernier_temps = 0

        self.broker = broker
        self.port = port
        self.sujet_log = sujet_log


        self.client = mqtt.Client()
        self.client.connect(self.broker, self.port, 60)

        # Création du fichier CSV avec en-tête s'il n'existe pas encore
        if not os.path.exists(nom_fichier):
            with open(nom_fichier, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Date/Heure", "UID", "Nom", "Statut"])

        print("Lecteur RFID prêt. Approchez une carte !")

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
    def afficher_carte(self, uid):
        #uid_hex = ' '.join(f'{octet:02X}' for octet in uid)
        print("\n####### Nouvelle carte détectée #######")
    
        print(f"UID  : {uid}")
        print("****************************************")

    def _verifier_carte(self, uid):
        est_autorisee, nom, message, _, _ = self.gestion_csv.verifier_carte(uid)
        
        if est_autorisee:
            return True, nom, "Accepte"
        else:
            return False, nom, message

    # Fonction pour enregistrer dans le CSV 
    def enregistrer(self, uid, nom, statut):
        date = time.strftime("%Y-%m-%d %H:%M:%S")
        uid_str = "-".join(str(octet) for octet in uid)
        
        with open(self.nom_fichier, 'a', newline='', encoding='utf-8') as fichier_csv:
            writer = csv.writer(fichier_csv)
            writer.writerow([date, uid_str, nom, statut])

    def publier_info_carte(self, date, uid):
        uid_str = "-".join(str(octet) for octet in uid)
        info_carte = json.dumps({
            "date_heure": date,
            "uid": uid_str
        })
        sujet_carte = f"{self.sujet_log}/{int(time.time())}"
        try:
            self.client.publish(sujet_carte, info_carte, qos=1, retain=False)
            self.client.loop()
            print(f"info carte envoye sur {self.sujet_log} : {info_carte}")
        except Exception as e:
            print(f"[AVERTISSEMENT] Erreur lors de la publication MQTT: {e}")

    def interface_admin(self, uid_admin):
        print("\n=== Mode Admin activé ===")

        while True:
            print("\nOptions :")
            print("1. Configurer une carte")
            print("2. Quitter")
            choix = input("Votre choix: ")

            if choix == "1":
                print("Veuillez approcher la carte à configurer...")

                uid_carte = None
                while uid_carte is None:
                    (erreur, uid_carte) = self.rfid.request()
                    if erreur:
                        time.sleep(0.1)
                        continue

                    (erreur, uid_carte_tmp) = self.rfid.anticoll()
                    if not erreur:
                        uid_carte = uid_carte_tmp

                uid_str = "-".join(str(octet) for octet in uid_carte)
                print(f"Carte détectée : {uid_str}")

                # On vérifie si elle existe déjà dans le CSV
                existe, nom_actuel, _, _, _ = self.gestion_csv.verifier_carte(uid_str)
                
                # Si le nom n'est pas "Non renseigné", c'est qu'elle existe (même si inactive)
                carte_trouvee = (nom_actuel != "Non renseigné")

                if carte_trouvee:
                    print(f"Carte existante : Nom = {nom_actuel}")
                    confirmation = input("Cette carte existe, voulez-vous écraser ses informations ? (oui/non) : ")
                    
                    if confirmation.lower() == "oui":
                        nouveau_nom = input("Entrez le nom de la carte : ").strip()
                        statut_actif = input("Activer la carte ? (oui/non) : ").strip().lower() == "oui"
                        
                        # Appel CSV pour mise à jour
                        self.gestion_csv.ajouter_ou_modifier_carte(uid_str, nouveau_nom, statut_actif)
                    else:
                        print("Configuration non modifiée.")

                else:
                    # Nouvelle carte
                    print("Nouvelle carte détectée.")
                    nouveau_nom = input("Entrez le nom de la carte : ").strip()
                    statut_actif = input("Activer la carte ? (oui/non) : ").strip().lower() == "oui"
                    
                    # Appel CSV pour ajout
                    self.gestion_csv.ajouter_ou_modifier_carte(uid_str, nouveau_nom, statut_actif)

                self.menu_configuration_blocs(uid_carte)

            elif choix == "2":
                print("Sortie du mode Admin.")
                break
            else:
                print("Choix invalide, réessayez.")



    def menu_configuration_blocs(self, uid_admin):

        while True:
            print("\n--- Menu Bloc ---")
            print("1. Lire un bloc")
            print("2. Écrire un bloc")
            print("3. Quitter le menu bloc")
            choix = input("Votre choix : ")

            if choix == "1":
                bloc = int(input("Numéro du bloc à lire : "))
                
                if self.mifare.est_bloc_remorque(bloc):
                    print(f"[INFO] Bloc {bloc} est un bloc remorque, lecture impossible")
                    continue

                uid_carte = self.attendre_carte()

                contenu = self.mifare.lire_bloc(uid_carte, bloc)
                #print(f"Contenu du bloc {bloc} : {contenu}")
                if contenu is None:
                    print(f"[ERREUR] Impossible de lire le bloc {bloc}. Vérifie la clé ou le bloc.")
                else:
                    print(f"Contenu du bloc {bloc} : {contenu}")

            elif choix == "2":
                bloc = int(input("Numéro du bloc à écrire : "))

                if self.mifare.est_bloc_remorque(bloc):
                    print(f"[ERREUR] Impossible d’écrire dans un bloc remorque ({bloc}) !")
                    continue

                texte = input("Texte à écrire (max 16 caractères) : ")

                uid_carte = self.attendre_carte()

                if not uid_carte:
                    print("Aucune carte detectee.")
                    continue

                succes = self.mifare.ecrire_bloc(uid_carte, bloc, texte)
                if succes:
                    # Contenu réel déjà affiché dans ecrire_bloc()
                    print(f"[INFO] Écriture confirmée sur le bloc {bloc}: {succes}")
                else:
                    print(f"[ERREUR] Écriture impossible sur le bloc {bloc}. Vérifie la clé ou le bloc.")


            elif choix == "3":
                print("Retour au menu admin.")
                break
            else:
                print("Choix invalide, réessayez.")

    
    

    def attendre_carte(self):
        print("Approchez une carte…")
        while True:
            (error, uid) = self.mifare.rdr.request()
            if not error:
                (error, uid) = self.mifare.rdr.anticoll()
                if not error:
                    #print(f"Carte détectée : {uid}")
                    return uid
            time.sleep(0.1)


    def _charger_questions_admin(self, fichier_pass="pass.json") -> Dict:
        """Charge les questions pour les cartes admin."""
        if not os.path.exists(fichier_pass):
            print(f"[INFO] Fichier de questions {fichier_pass} non trouvé")
            return {}
        
        try:
            with open(fichier_pass, 'r', encoding='utf-8') as f:
                data = json.load(f)
            questions = {}
            for entry in data.get("pass", []):
                uid = entry.get("uid")
                if uid:
                    questions[uid] = {
                        "nom": entry.get("nom", "Admin"),
                        "question": entry.get("question", ""),
                        "reponse": entry.get("reponse", "")
                    }
            return questions
        except Exception as e:
            print(f"[ERREUR] Chargement questions admin: {e}")
            return {}


    # Boucle principale 
    def lancer(self):
        print("En attente d’une carte...")
        if self.ecran:
            self.ecran.accueil()

        try:

            while True:
                uid_carte = self.attendre_carte()
                                                                                                                                                                                                                                            
                # Normaliser l'UID
                #uid_str = "-".join(str(octet) for octet in uid_carte)
                #print(f"Carte détectée : {uid_str}")


                temps_actuel = time.time()

                # Vérification de la carte
                uid_string = "-".join(str(octet) for octet in uid_carte)
                est_autorisee, nom, statut = self._verifier_carte(uid_string)
                
                # Affichage + bip + enregistrement
                date = time.strftime("%Y-%m-%d %H:%M:%S")
                self.afficher_carte(uid_carte)
                print(f"Nom: {nom}")
                print(f"Statut: {statut}")
                
                if self.derniere_carte == uid_string and (temps_actuel - self.dernier_temps) < self.delai_lecture:
                    print("Cette carte a déjà été utilisée il y a moins de 5 secondes, veuillez patienter un peu...")
                    time.sleep(0.5)
                    continue
                

                print("\n===== Carte détectée =====")
                print("UID :", uid_carte)

                # Vérification d’accès
                carte_ok, nom_utilisateur = identifier_carte(uid_carte)

                if carte_ok:
                    self.acces.carte_acceptee(nom=nom_utilisateur)
                    acces = "accepte"
                    # On affiche un message sur l'écran <--- AJOUT
                    # On suppose que identifier_carte affiche le nom.
                    # self.ecran.afficher(
                    #     ligne1="ACCES ACCEPTE", 
                    #     ligne2="Bienvenue!", 
                    #     duree=2
                    # )
                else:
                    self.acces.carte_refusee()
                    acces = "refuse"
                    # On affiche un message d'erreur sur l'écran <--- AJOUT
                    # self.ecran.afficher(
                    #     ligne1="ACCES REFUSE", 
                    #     ligne2="Carte invalide", 
                    #     duree=2
                    # )

                if est_autorisee and nom.lower() == "admin":
                    question_data = self.questions_admin.get(uid_string)
                    if question_data:
                        print(f"[SECURITE] Question pour admin : {question_data['question']}")

                # Mémorisation pour éviter les doublons..............................................................
                        self.derniere_carte = uid_string
                        tentatives = 3
                        while tentatives > 0:
                            reponse = input("Votre réponse : ").strip()
                            if reponse.lower() == question_data['reponse'].strip().lower():
                                print("[INFO] Réponse correcte. Accès admin autorisé.")
                                self.interface_admin(uid_carte)
                                break
                            else:
                                tentatives -= 1
                                print(f"[ALERTE] Réponse incorrecte. Il vous reste {tentatives} tentatives.")
                        if tentatives == 0:
                            print("[ALERTE] Accès admin refusé définitivement.")

                    else:
                        print("[INFO] Pas de question de sécurité trouvée. Accès admin autorisé.")
                        self.interface_admin(uid_carte)

                        
                        self.publier_info_carte(date, uid_carte)
                        self.enregistrer(uid_carte, nom, statut)


                # Mémorisation de la dernière carte
                #self.derniere_carte = uid
                self.derniere_carte = uid_string
                self.dernier_temps = temps_actuel

        finally:
            try:
                GPIO.cleanup()
            except RuntimeWarning:
                pass
            self.rfid.cleanup()
            print(" Nettoyage terminé.")



