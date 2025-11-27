from pirc522 import RFID
import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt
import time
import csv
import os
import json
import sys
from typing import Dict
from card_reader import CardReader


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
                 utiliser_mqtt = True                 
              ):
      
        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)
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
        self.cartes_autorisees = self._charger_cartes_autorisees()
        self.mifare = CardReader()
        self.questions_admin = self._charger_questions_admin("pass.json")


        # Mémorise la dernière carte lue 
        self.derniere_carte = None
        self.dernier_temps = 0

        self.broker = broker
        self.port = port
        self.sujet_log = sujet_log
        self.utiliser_mqtt = utiliser_mqtt

        if utiliser_mqtt:
            self.client = mqtt.Client()
            try:
                self.client.connect(self.broker, self.port, 60)
            except Exception as e:
                print(f"[AVERTISSEMENT] Impossible de se connecter au broker MQTT: {e}")
                print("[INFO] Le lecteur fonctionnera sans MQTT.")
                self.utiliser_mqtt = False
        else:
            self.client = None

        # Création du fichier CSV avec en-tête s'il n'existe pas encore
        if not os.path.exists(nom_fichier):
            with open(nom_fichier, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Date/Heure", "Type de carte", "UID", "Nom", "Statut"])

        print("Lecteur RFID prêt. Approchez une carte !")

    def _charger_cartes_autorisees(self) -> Dict:
        if not os.path.exists(self.fichier_cartes):
            print(f"Le fichier {self.fichier_cartes} n'existe pas")
            sys.exit(1)
        
        try:
            with open(self.fichier_cartes, 'r', encoding='utf-8') as fichier:
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
                return True, carte_info['nom'], "Accepte"
            else:
                return False, carte_info['nom'], "Carte desactivee"
        else:
            return False, "Non renseigne", "Refuse - Carte non autorisee"

    # Fonction pour enregistrer dans le CSV 
    def enregistrer(self, type_carte, uid, nom, statut):
        date = time.strftime("%Y-%m-%d %H:%M:%S")
        uid_str = "-".join(str(octet) for octet in uid)
        
        with open(self.nom_fichier, 'a', newline='', encoding='utf-8') as fichier_csv:
            writer = csv.writer(fichier_csv)
            writer.writerow([date, type_carte, uid_str, nom, statut])

    def publier_info_carte(self, date, type_carte, uid):
        if not self.utiliser_mqtt or self.client is None:
            return
        uid_str = "-".join(str(octet) for octet in uid)
        info_carte = json.dumps({
            "date_heure": date,
            "type_carte": type_carte,
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
                    (erreur, type_carte) = self.rfid.request()
                    if erreur:
                        time.sleep(0.1)
                        continue

                    (erreur, uid_carte_tmp) = self.rfid.anticoll()
                    if not erreur:
                        uid_carte = uid_carte_tmp

                uid_str = "-".join(str(octet) for octet in uid_carte)
                print(f"Carte détectée : {uid_str}")

                # Vérification si la carte existe déjà
                if uid_str in self.cartes_autorisees:
                    carte_info = self.cartes_autorisees[uid_str]
                    print(f"Carte existante : Nom = {carte_info['nom']}, Actif = {carte_info['actif']}")
                    confirmation = input("Cette carte existe, voulez-vous écraser ses informations ? (oui/non) : ")
                    
                    if confirmation.lower() == "oui":
                        nouveau_nom = input("Entrez le nom de la carte : ").strip()
                        statut_actif = input("Activer la carte ? (oui/non) : ").strip().lower() == "oui"
                        self.cartes_autorisees[uid_str] = {
                            "nom": nouveau_nom,
                            "actif": statut_actif
                        }
                        self._sauvegarder_cartes()
                        print(f"Carte {uid_str} configurée : Nom = {nouveau_nom}, Actif = {statut_actif}")
                    else:
                        print("Configuration non modifiée.")
                        nouveau_nom = carte_info['nom']
                        statut_actif = carte_info['actif']

                else:
                    # Nouvelle carte
                    print("Nouvelle carte détectée.")
                    nouveau_nom = input("Entrez le nom de la carte : ").strip()
                    statut_actif = input("Activer la carte ? (oui/non) : ").strip().lower() == "oui"
                    self.cartes_autorisees[uid_str] = {
                        "nom": nouveau_nom,
                        "actif": statut_actif
                    }
                    self._sauvegarder_cartes()
                    print(f"Carte {uid_str} configurée : Nom = {nouveau_nom}, Actif = {statut_actif}")


                self.menu_configuration_blocs(uid_carte)

            elif choix == "2":
                print("Sortie du mode Admin.")
                break
            else:
                print("Choix invalide, réessayez.")



    def menu_configuration_blocs(self, uid):

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

                contenu = self.mifare.lire_bloc(uid, bloc)
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
                succes = self.mifare.ecrire_bloc(uid, bloc, texte)
                if succes:
                    print(f"[INFO] Écriture réussie sur le bloc {bloc}")
                else:
                    print(f"[ERREUR] Écriture impossible sur le bloc {bloc}. Vérifie la clé ou le bloc.")


            elif choix == "3":
                print("Retour au menu admin.")
                break
            else:
                print("Choix invalide, réessayez.")


    def _sauvegarder_cartes(self):
        """Sauvegarde le dictionnaire des cartes autorisées dans le fichier JSON."""
        data = {"cartes": []}
        for uid, info in self.cartes_autorisees.items():
            data["cartes"].append({
                "uid": uid,
                "nom": info["nom"],
                "actif": info["actif"]
            })
        try:
            with open(self.fichier_cartes, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            print("[INFO] Fichier JSON mis à jour avec succès.")
        except Exception as e:
            print(f"[ERREUR] Impossible de sauvegarder le fichier JSON : {e}")


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
        print(" En attente d’une carte...")

        try:

            while True:
                #self.rfid.wait_for_tag()
                (erreur, type_carte) = self.rfid.request()
                if erreur:
                    time.sleep(0.1)
                    continue


                (erreur, uid_carte) = self.rfid.anticoll()
                if erreur:
                    continue
                # Normaliser l'UID
                uid_str = "-".join(str(octet) for octet in uid_carte)
                print(f"Carte détectée : {uid_str}")


                temps_actuel = time.time()

                # Vérification de la carte
                uid_string = "-".join(str(octet) for octet in uid_carte)
                est_autorisee, nom, statut = self._verifier_carte(uid_string)
                
                # Affichage + bip + enregistrement
                date = time.strftime("%Y-%m-%d %H:%M:%S")
                self.afficher_carte(type_carte, uid_carte)
                print(f"Nom: {nom}")
                print(f"Statut: {statut}")
                
                if self.derniere_carte == uid_string and (temps_actuel - self.dernier_temps) < self.delai_lecture:
                    print("Cette carte a déjà été utilisée il y a moins de 5 secondes, veuillez patienter un peu...")
                    time.sleep(0.5)
                    continue
                

                if est_autorisee:
                    GPIO.output(self.led_verte, GPIO.HIGH)
                    self.bip(0.2)  
                    GPIO.output(self.led_verte, GPIO.LOW)
                else:
                    GPIO.output(self.led_rouge, GPIO.HIGH)
                    self.bip(0.8)  
                    GPIO.output(self.led_rouge, GPIO.LOW)

                if est_autorisee and nom.lower() == "admin":
                    question_data = self.questions_admin.get(uid_string)
                    if question_data:
                        print(f"[SECURITE] Question pour admin : {question_data['question']}")

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

                
                self.publier_info_carte(date, type_carte, uid_carte)
                self.enregistrer(type_carte, uid_carte, nom, statut)


                # Mémorisation de la dernière carte
                #self.derniere_carte = uid
                self.derniere_carte = uid_string
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



