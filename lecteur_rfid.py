from pirc522 import RFID
import RPi.GPIO as GPIO
import paho.mqtt.client as mqtt
import time
import csv
import os
import json
import sys
from typing import Dict

from gestion_acces import GestionAcces           
from verification import identifier_carte        
from affichage_qapass import AffichageQapass
from configuration_carte import CarteConfiguration
from cartes_autorisees import GestionCartesCSV

class LecteurRFID:

    def __init__(self,
                 broche_buzzer=33,
                 delai_lecture=2,
                 nom_fichier="journal_rfid.csv",
                 led_rouge=38,
                 led_verte=40,
                 broker="10.4.1.162",
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

        GPIO.setup(self.led_verte, GPIO.OUT) 
        GPIO.setup(self.led_rouge, GPIO.OUT) 
        GPIO.setup(self.buzzer, GPIO.OUT)    

        self.ecran = AffichageQapass()

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

        self.derniere_carte = None
        self.dernier_temps = 0
        self.broker = broker
        self.port = port
        self.sujet_log = sujet_log

        self.client = mqtt.Client()
        try:
            self.client.connect(self.broker, self.port, 60)
        except:
            print("Erreur connexion MQTT")

        if not os.path.exists(nom_fichier):
            with open(nom_fichier, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Date/Heure", "UID", "Nom", "Statut"])

        print("Lecteur RFID prêt. Approchez une carte !")

    def bip(self, duree=0.3):
        GPIO.output(self.buzzer, True)
        time.sleep(duree)
        GPIO.output(self.buzzer, False)

    def afficher_carte(self, uid):
        print("\n####### Nouvelle carte détectée #######")
        print(f"UID  : {uid}")
        print("****************************************")

    def _verifier_carte(self, uid):
        est_autorisee, nom, message, _, _ = self.gestion_csv.verifier_carte(uid)
        if est_autorisee:
            return True, nom, "Accepte"
        else:
            return False, nom, message

    def enregistrer(self, uid, nom, statut):
        date = time.strftime("%Y-%m-%d %H:%M:%S")
        uid_str = "-".join(str(octet) for octet in uid)
        with open(self.nom_fichier, 'a', newline='', encoding='utf-8') as fichier_csv:
            writer = csv.writer(fichier_csv)
            writer.writerow([date, uid_str, nom, statut])

    def publier_info_carte(self, date, uid):
        uid_str = "-".join(str(octet) for octet in uid)
        info_carte = json.dumps({"date_heure": date, "uid": uid_str})
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
            print("1. Configurer une carte (Ajout/Modif + Écriture Blocs)")
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

                # Vérification existence
                existe, nom_actuel, _, _, _ = self.gestion_csv.verifier_carte(uid_str)
                carte_trouvee = (nom_actuel != "Non renseigné")

                # Valeurs par défaut
                nouveau_nom = nom_actuel if carte_trouvee else ""
                statut_actif = True
                nouveaux_credits = "0"
                
                # --- SAISIE DES DONNÉES ---
                if carte_trouvee:
                    print(f"Carte existante : Nom = {nom_actuel}")
                    conf = input("Écraser ? (oui/non) : ")
                    if conf.lower() == "oui":
                        nouveau_nom = input("Nom : ").strip()
                        statut_actif = input("Activer ? (oui/non) : ").strip().lower() == "oui"
                        nouveaux_credits = input("Crédits : ").strip()
                    else:
                        print("Annulé.")
                        continue
                else:
                    print("Nouvelle carte.")
                    nouveau_nom = input("Nom : ").strip()
                    statut_actif = input("Activer ? (oui/non) : ").strip().lower() == "oui"
                    nouveaux_credits = input("Crédits : ").strip()

                if not nouveaux_credits: nouveaux_credits = "0"

                # --- 1. SAUVEGARDE CSV ---
                succes, id_genere = self.gestion_csv.ajouter_ou_modifier_carte(
                    uid_str, nouveau_nom, statut_actif, nouveaux_credits
                )

                # --- 2. ÉCRITURE PHYSIQUE ---
                if succes and id_genere:
                    print(f"\n[ÉCRITURE] Enregistrement sur la puce RFID...")
                    print(f" -> Bloc 4 (ID) : {id_genere}")
                    print(f" -> Bloc 5 (Crédits) : {nouveaux_credits}")
                    
                    # Message explicite pour demander de rescanner
                    # On utilise la nouvelle fonction attendre_carte avec message
                    uid_pour_ecriture = self.attendre_carte(
                        message=">>> Veuillez RESCANNER la carte maintenant pour finaliser l'écriture... <<<"
                    )

                    # 1. Écriture ID (Bloc 4)
                    ok_id = self.mifare.ecrire_bloc(uid_pour_ecriture, 4, str(id_genere))
                    
                    time.sleep(0.2)
                    
                    # 2. Écriture Crédits (Bloc 5)
                    # On ré-attend la carte silencieusement (car elle est surement déjà là) ou avec un petit message
                    uid_pour_ecriture = self.attendre_carte(message=None) 
                    ok_cred = self.mifare.ecrire_bloc(uid_pour_ecriture, 5, str(nouveaux_credits))

                    if ok_id and ok_cred:
                        print("[SUCCÈS] Carte entièrement configurée (CSV + Puce) !")
                    else:
                        print("[ATTENTION] Une des écritures a échoué. Vérifiez les blocs.")
                
                self.menu_configuration_blocs(uid_carte)

            elif choix == "2":
                print("Sortie du mode Admin.")
                break
            else:
                print("Choix invalide.")

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
                    print("Lecture bloc remorque impossible")
                    continue
                
                # Ajout du message ici
                uid_carte = self.attendre_carte("Approchez la carte à lire...")
                
                contenu = self.mifare.lire_bloc(uid_carte, bloc)
                if contenu: print(f"Contenu : {contenu}")

            elif choix == "2":
                bloc = int(input("Numéro du bloc à écrire : "))
                if self.mifare.est_bloc_remorque(bloc):
                    print("Écriture bloc remorque interdite")
                    continue
                texte = input("Texte : ")
                
                # Ajout du message ici
                uid_carte = self.attendre_carte("Approchez la carte pour écrire...")
                
                self.mifare.ecrire_bloc(uid_carte, bloc, texte)

            elif choix == "3":
                break

    # --- MODIFICATION ICI : On accepte un message personnalisé ---
    def attendre_carte(self, message="Approchez une carte..."):
        if message:
            print(message)
            
        while True:
            (error, uid) = self.mifare.rdr.request()
            if not error:
                (error, uid) = self.mifare.rdr.anticoll()
                if not error:
                    return uid
            time.sleep(0.1)

    def _charger_questions_admin(self, fichier_pass="pass.json") -> Dict:
        if not os.path.exists(fichier_pass): return {}
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
        except: return {}

    def lancer(self):
        print("En attente d’une carte...")
        if self.ecran: self.ecran.accueil()
        try:
            while True:
                # Ici on garde le message par défaut ou on met None si on veut silence
                uid_carte = self.attendre_carte(message=None) 
                
                temps_actuel = time.time()
                uid_string = "-".join(str(octet) for octet in uid_carte)
                est_autorisee, nom, statut = self._verifier_carte(uid_string)
                date = time.strftime("%Y-%m-%d %H:%M:%S")
                
                self.afficher_carte(uid_carte)
                print(f"Nom: {nom}")
                print(f"Statut: {statut}")
                
                if self.derniere_carte == uid_string and (temps_actuel - self.dernier_temps) < self.delai_lecture:
                    time.sleep(0.5)
                    continue

                print("\n===== Carte détectée =====")
                print("UID :", uid_carte)

                carte_ok, nom_utilisateur = identifier_carte(uid_carte)
                if carte_ok:
                    self.acces.carte_acceptee(nom=nom_utilisateur)
                else:
                    self.acces.carte_refusee()

                if est_autorisee and nom.lower() == "admin":
                    question_data = self.questions_admin.get(uid_string)
                    if question_data:
                        print(f"[SECURITE] Question : {question_data['question']}")
                        self.derniere_carte = uid_string
                        tentatives = 3
                        while tentatives > 0:
                            reponse = input("Réponse : ").strip()
                            if reponse.lower() == question_data['reponse'].strip().lower():
                                print("Accès admin autorisé.")
                                self.interface_admin(uid_carte)
                                break
                            else:
                                tentatives -= 1
                                print(f"Incorrect. Restantes: {tentatives}.")
                    else:
                        print("Accès admin autorisé.")
                        self.interface_admin(uid_carte)
                        self.publier_info_carte(date, uid_carte)
                        self.enregistrer(uid_carte, nom, statut)

                self.derniere_carte = uid_string
                self.dernier_temps = temps_actuel
        finally:
            GPIO.cleanup()
            self.rfid.cleanup()
            print(" Nettoyage terminé.")