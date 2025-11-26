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

from card_manager import CardService, ReadError
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
                 fichier_cartes_csv = "cartes_autorisees.csv"
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
        self.fichier_cartes_csv = fichier_cartes_csv
        self.cartes_autorisees = self._charger_cartes_autorisees()
        
        # Initialisation gestion CSV
        self.gestion_acces = GestionAcces(self.fichier_cartes_csv)
        
        # Initialisation Lecteur Mifare (pour les blocs)
        self.mifare = CardReader()
        
        self.questions_admin = self._charger_questions_admin("pass.json")


        # Mémorise la dernière carte lue 
        self.derniere_carte = None
        self.dernier_temps = 0

        self.broker = broker
        self.port = port
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
        print("\n####### Nouvelle carte détectée #######")
        print(f"Type : {type_carte}")
        print(f"UID  : {uid}")
        print("****************************************")
        
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

    # --- Petite fonction aide pour sortir la logique admin de la boucle principale ---
    def _gerer_admin(self, uid_string, uid_carte):
        question_data = self.questions_admin.get(uid_string)
        if question_data:
            print(f"[SECURITE] Question pour admin : {question_data['question']}")
            tentatives = 3
            while tentatives > 0:
                reponse = input("Votre réponse : ").strip()
                if reponse.lower() == question_data['reponse'].strip().lower():
                    print("[INFO] Accès admin autorisé.")
                    self.interface_admin(uid_carte)
                    break
                else:
                    tentatives -= 1
                    print(f"Incorrect. Reste {tentatives} essais.")
        else:
            self.interface_admin(uid_carte)

    # --- Boucle principale ---
    def lancer(self):
        print(" En attente d’une carte...")

        try:
            while True:
                # 1. DETECTION (PIRC522)
                (erreur, type_carte) = self.rfid.request()
                if erreur:
                    time.sleep(0.1)
                    continue

                (erreur, uid_carte) = self.rfid.anticoll()
                if erreur:
                    continue
                
                # Normaliser l'UID
                uid_str = "-".join(str(octet) for octet in uid_carte)
                temps_actuel = time.time()

                # 2. ANTI-REBOND (Si c'est la même carte qu'il y a 2 sec, on ignore)
                if self.derniere_carte == uid_str and (temps_actuel - self.dernier_temps) < self.delai_lecture:
                    continue
                
                print(f"Carte détectée : {uid_str}")

                # 3. LECTURE DES BLOCS PHYSIQUES (MFRC522)
                # On essaie de lire les infos fraîches sur la carte
                print("Tentative de lecture des blocs internes...")
                
                # Valeurs par défaut si la lecture échoue
                id_lu_carte = ""     
                credits_lu_carte = 0 

                try:
                    # On utilise self.mifare qui est déjà initialisé (plus sûr)
                    service_carte = CardService(self.mifare)
                    
                    # Lecture ID (Bloc 4)
                    try:
                        id_lu_carte = service_carte.read_card_id(uid_carte)
                        print(f"-> ID lu sur la carte : {id_lu_carte}")
                    except ReadError:
                        print("-> Impossible de lire l'ID (Bloc 4) ou carte vide")

                    # Lecture Crédits (Bloc 5)
                    try:
                        credits_lu_carte = service_carte.read_counter(uid_carte)
                        print(f"-> Crédits lus sur la carte : {credits_lu_carte}")
                    except ReadError:
                        print("-> Impossible de lire les Crédits (Bloc 5)")

                    # 4. MISE A JOUR DU CSV
                    # On sauvegarde immédiatement ce qu'on a lu dans le fichier
                    if id_lu_carte or credits_lu_carte:
                        self.gestion_acces.mettre_a_jour_infos(uid_str, credits_lu_carte, id_lu_carte)

                except Exception as e:
                    print(f"Conflit technique lecture blocs (normal en mode hybride) : {e}")

                # 5. VERIFICATION ET DECISION
                # Maintenant que le CSV est à jour, on vérifie si on ouvre
                est_autorisee, nom, statut, credits_csv, id_perso_csv = self.gestion_acces.verifier_carte(uid_str)

                # Affichage console
                date = time.strftime("%Y-%m-%d %H:%M:%S")
                self.afficher_carte(type_carte, uid_carte)
                print(f"Nom: {nom}")
                print(f"ID Carte : {id_perso_csv}")
                print(f"Crédits  : {credits_csv}")
                print(f"Statut   : {statut}")
                
                # 6. ACTION (LED + BIP)
                if est_autorisee:
                    self.gestion_led(0.3) 
                    # Gestion Admin
                    if nom.lower() == "admin":
                        self._gerer_admin(uid_str, uid_carte)
                else:
                    GPIO.output(self.led_rouge, GPIO.HIGH)
                    self.bip(0.8)  
                    GPIO.output(self.led_rouge, GPIO.LOW)

                # 7. LOG
                self.publier_info_carte(date, type_carte, uid_carte)
                self.enregistrer(type_carte, uid_carte, nom, statut)

                # Mémorisation
                self.derniere_carte = uid_str
                self.dernier_temps = temps_actuel

        except KeyboardInterrupt:
            print("\n Arrêt du programme.")
        finally:
            try:
                GPIO.cleanup()
            except RuntimeWarning:
                pass
            self.rfid.cleanup()
            print(" Nettoyage terminé.")