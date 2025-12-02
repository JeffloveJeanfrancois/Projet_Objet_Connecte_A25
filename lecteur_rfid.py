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

# Tes modules personnels
from carte_autorise import GestionAcces
from card_manager import CardService, ReadError
from configuration_carte import CarteConfiguration

class LecteurRFID:

    def __init__(self, 
                 broche_buzzer=33, 
                 delai_lecture=2, 
                 nom_fichier = "journal_rfid.csv",
                 led_rouge = 38,
                 led_verte = 40,
                 broker = "10.4.1.164",
                 port = 1883,
                 sujet_log = "LecteurRFID/log",
                 fichier_cartes_csv = "cartes_autorisees.csv",
                 fichier_pass = "pass.json",
                 utiliser_mqtt = True                 
              ):
      
        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)
        GPIO.setup(broche_buzzer, GPIO.OUT)
        GPIO.setup(led_rouge, GPIO.OUT)
        GPIO.setup(led_verte, GPIO.OUT)

        # On garde PIRC522 (pin_irq=None pour polling)
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
        self.fichier_cartes_csv = fichier_cartes_csv
        
        # Initialisation gestion CSV
        self.gestion_acces = GestionAcces(self.fichier_cartes_csv)
        
        # Initialisation de ta configuration carte (qui utilise self.rfid)
        self.mifare = CarteConfiguration(rdr=self.rfid)
        
        # On charge SEULEMENT les questions admin du JSON
        self.questions_admin = self._charger_questions_admin(fichier_pass)

        self.derniere_carte = None
        self.dernier_temps = 0

        self.broker = broker
        self.port = port
        self.sujet_log = sujet_log
        self.client = None

        if utiliser_mqtt:
            try:
                self.client = mqtt.Client()
                self.client.connect(self.broker, self.port, 60)
            except Exception as e:
                print(f"[WARN] MQTT non connecté : {e}")

        # Création du journal CSV s'il n'existe pas
        if not os.path.exists(nom_fichier):
            with open(nom_fichier, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Date/Heure", "UID", "Nom", "Statut"])

        print("Lecteur RFID prêt (PIRC522 + CSV + Écriture Blocs).")

    def bip(self, duree=0.3):
        GPIO.output(self.buzzer, True)
        time.sleep(duree)
        GPIO.output(self.buzzer, False)

    def gestion_led(self, duree=0.3):
        GPIO.output(self.led_verte, GPIO.HIGH)
        time.sleep(duree)
        GPIO.output(self.led_verte, GPIO.LOW)

    def afficher_carte(self, uid):
        uid_str = "-".join(str(octet) for octet in uid)
        print("\n####### Nouvelle carte détectée #######")
        print(f"UID  : {uid_str}")
        print("****************************************")

    def enregistrer(self, uid, nom, statut):
        date = time.strftime("%Y-%m-%d %H:%M:%S")
        uid_str = "-".join(str(octet) for octet in uid)
        
        with open(self.nom_fichier, 'a', newline='', encoding='utf-8') as fichier_csv:
            writer = csv.writer(fichier_csv)
            writer.writerow([date, uid_str, nom, statut])

    def publier_info_carte(self, date, uid):
        if not self.client: return
        uid_str = "-".join(str(octet) for octet in uid)
        info_carte = json.dumps({"date_heure": date, "uid": uid_str})
        sujet_carte = f"{self.sujet_log}/{int(time.time())}"
        try:
            self.client.publish(sujet_carte, info_carte, qos=1, retain=False)
        except Exception:
            pass

    def attendre_carte(self):
        """Fonction bloquante pour attendre une carte"""
        print("Approchez une carte...")
        while True:
            (error, tag_type) = self.rfid.request()
            if not error:
                (error, uid) = self.rfid.anticoll()
                if not error:
                    return uid
            time.sleep(0.1)

    def _generer_prochain_id(self):
        max_id = 0
        if os.path.exists(self.fichier_cartes_csv):
            with open(self.fichier_cartes_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    id_courant = row.get("Id", "")
                    if id_courant.startswith("USER-"):
                        try:
                            valeur = int(id_courant.split("-")[1])
                            if valeur > max_id:
                                max_id = valeur
                        except:
                            pass
        return f"USER-{max_id + 1}"

    def interface_admin(self, uid_admin):
        print("\n=== Mode Admin activé ===")
        while True:
            print("\nOptions :")
            print("1. Configurer une carte (Ajouter/Modifier)")
            print("2. Quitter")
            choix = input("Votre choix: ")

            if choix == "1":
                uid_carte = self.attendre_carte()
                uid_str = "-".join(str(o) for o in uid_carte)
                print(f"Carte détectée : {uid_str}")

                existe, nom_actuel, _, _, _ = self.gestion_acces.verifier_carte(uid_str)

                # --- VARIABLES ---
                nouveau_nom = nom_actuel
                nouveau_statut = True
                nb_credits = 0

                if existe:
                    print(f"Carte connue : {nom_actuel}")
                    if input("Modifier ? (o/n) : ").lower() == 'o':
                        nouveau_nom = input("Nom : ").strip()
                        nouveau_statut = input("Activer ? (o/n) : ").lower() == 'o'
                        
                        try:
                            nb_credits = int(input("Nouveaux crédits : "))
                        except ValueError:
                            print("Erreur de saisie, crédits mis à 0")
                            nb_credits = 0
                            
                        print("Mise à jour des crédits sur la carte (Bloc 5)...")
                        self.mifare.ecrire_bloc(uid_carte, 5, str(nb_credits))
                        self.gestion_acces.ajouter_ou_modifier_carte(uid_str, nouveau_nom, nouveau_statut)
                else:
                    print("Nouvelle carte !")
                    nouveau_nom = input("Nom : ").strip()
                    nouveau_statut = input("Activer ? (o/n) : ").lower() == 'o'
                    
                    try:
                        nb_credits = int(input("Combien de crédits initial ? : "))
                    except ValueError:
                        print("Erreur, crédits = 0")
                        nb_credits = 0
                    
                    nouvel_id = self._generer_prochain_id()
                    print(f"Génération du nouvel ID : {nouvel_id}")
                    
                    print("Écriture sur la carte en cours...")
                    if self.mifare.ecrire_bloc(uid_carte, 4, nouvel_id):
                        print("-> Bloc 4 (ID) écrit OK.")
                    else:
                        print("-> Erreur écriture ID !")

                    if self.mifare.ecrire_bloc(uid_carte, 5, str(nb_credits)):
                        print(f"-> Bloc 5 (Crédits: {nb_credits}) écrit OK.")
                    else:
                        print("-> Erreur écriture Crédits !")

                    self.gestion_acces.ajouter_ou_modifier_carte(uid_str, nouveau_nom, nouveau_statut)
                    self.gestion_acces.mettre_a_jour_infos(uid_str, nb_credits, nouvel_id)
                    
                print("Configuration terminée.")
                time.sleep(1)

            elif choix == "2":
                print("--- Sortie du mode Admin... ---")
                time.sleep(1)
                break # Sort de la boucle while du mode admin, retourne à _gerer_admin

    def _charger_questions_admin(self, fichier_pass) -> Dict:
        if not os.path.exists(fichier_pass):
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
            print(f"Erreur chargement pass.json: {e}")
            return {}

    def _gerer_admin(self, uid_str, uid_carte):
        q_data = self.questions_admin.get(uid_str)
        if q_data:
            print(f"[SECURITE] Question : {q_data['question']}")
            tentatives = 3
            while tentatives > 0:
                rep = input("Réponse : ").strip()
                if rep.lower() == q_data['reponse'].strip().lower():
                    self.interface_admin(uid_carte)
                    # IMPORTANT : On réinitialise l'anti-rebond ici pour que le lecteur soit prêt
                    self.derniere_carte = None 
                    print("\n[INFO] Retour au mode lecture. Approchez une carte...")
                    return
                tentatives -= 1
                print(f"Incorrect ({tentatives} restants)")
        else:
            self.interface_admin(uid_carte)
            self.derniere_carte = None
            print("\n[INFO] Retour au mode lecture. Approchez une carte...")

    def lancer(self):
        print("En attente d’une carte...")
        if self.ecran:
            self.ecran.accueil()

        try:
            while True:
                # 1. Détection
                (error, tag_type) = self.rfid.request()
                if error: 
                    time.sleep(0.1)
                    continue
                
                (error, uid_carte) = self.rfid.anticoll()
                if error: continue

                uid_str = "-".join(str(o) for o in uid_carte)
                now = time.time()

                if self.derniere_carte == uid_str and (now - self.dernier_temps) < self.delai_lecture:
                    continue

                self.afficher_carte(uid_carte)

                # 2. Lecture des Blocs
                id_lu = ""
                credits_lu = 0
                
                # Bloc 4 : ID
                data_id = self.mifare.lire_bloc(uid_carte, 4)
                if data_id:
                    id_lu = ''.join(chr(x) for x in data_id if x != 0)
                    print(f"-> ID lu : {id_lu}")

                # Bloc 5 : Crédits
                data_cred = self.mifare.lire_bloc(uid_carte, 5)
                if data_cred:
                    try:
                        cred_str = "".join(chr(x) for x in data_cred if x != 0)
                        if cred_str:
                            credits_lu = int(cred_str)
                        else:
                            credits_lu = 0
                    except ValueError:
                        print("-> Format crédits invalide")
                        credits_lu = 0
                    print(f"-> Crédits lus : {credits_lu}")
                
                # Mise à jour du CSV si lecture OK
                if id_lu:
                    self.gestion_acces.mettre_a_jour_infos(uid_str, credits_lu, id_lu)

                # 3. Vérification Accès
                autorise, nom, statut, cr_csv, id_csv = self.gestion_acces.verifier_carte(uid_str)
                print(f"Résultat : {nom} ({statut})")

                # 4. Action
                if autorise:
                    self.gestion_led()
                    if "admin" in nom.lower():
                        self._gerer_admin(uid_str, uid_carte)
                else:
                    self.bip(0.8)
                    GPIO.output(self.led_rouge, GPIO.HIGH)
                    time.sleep(1)
                    GPIO.output(self.led_rouge, GPIO.LOW)

                # 5. Log
                self.enregistrer(uid_carte, nom, statut)
                self.publier_info_carte(time.strftime("%Y-%m-%d %H:%M:%S"), uid_carte)
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

                self.derniere_carte = uid_str
                self.dernier_temps = now

        except KeyboardInterrupt:
            print("Arrêt.")
        finally:
            GPIO.cleanup()
            self.rfid.cleanup()