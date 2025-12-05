from pirc522 import RFID
import time
import os
import json
from typing import Dict

from gestion_acces import GestionAcces
from verification import identifier_carte
from affichage_qapass import AffichageQapass
from rfid_lecteur import LecteurRFID
from card_manager import CardService
from cartes_autorisees import GestionCartesCSV
from journal_rfid import JournalRFID
from mqtt_publisher import MqttPublisher
from admin_interface import AdminInterface
from feedback import FeedbackGPIO


class RFIDController:
    def __init__(
        self,
        broche_buzzer=33,
        delai_lecture=2,
        nom_fichier="historique_acces.csv",
        led_rouge=38,
        led_verte=40,
        broker="broker-mqtt.canadaeast-1.ts.eventgrid.azure.net",
        port=8883,
        sujet_log="LecteurRFID/logs",
        fichier_cartes="cartes_autorisees.csv",
        utiliser_mqtt=True,
        mqtt_username=None,
        mqtt_certfile=None,
        mqtt_keyfile=None,
    ):
        self.rfid = RFID(pin_irq=None)
        self.feedback = FeedbackGPIO(
            led_verte=led_verte,
            led_rouge=led_rouge,
            buzzer=broche_buzzer
        )

        self.ecran = AffichageQapass()

        self.acces = GestionAcces(feedback=self.feedback, ecran=self.ecran)

        self.delai_lecture = delai_lecture
        self.nom_fichier = nom_fichier
        self.fichier_cartes = fichier_cartes
        self.gestion_csv = GestionCartesCSV(nom_fichier=self.fichier_cartes)
        self.mifare = LecteurRFID(rdr=self.rfid)
        self.card_service = CardService(self.mifare)
        self.questions_admin = self._charger_questions_admin("pass.json")

        self.derniere_carte = None
        self.dernier_temps = 0
        self.broker = broker
        self.port = port
        self.sujet_log = sujet_log
        self.utiliser_mqtt = utiliser_mqtt
        self.mqtt_username = mqtt_username
        self.mqtt_certfile = mqtt_certfile
        self.mqtt_keyfile = mqtt_keyfile

        self.journal = JournalRFID(nom_fichier=self.nom_fichier)
        self.mqtt_publisher = MqttPublisher(
            utiliser_mqtt=self.utiliser_mqtt,
            broker=self.broker,
            port=self.port,
            sujet_log=self.sujet_log,
            mqtt_username=self.mqtt_username,
            mqtt_certfile=self.mqtt_certfile,
            mqtt_keyfile=self.mqtt_keyfile,
        )
        self.admin_interface = AdminInterface(
            gestion_csv=self.gestion_csv,
            mifare=self.mifare,
            questions_admin=self.questions_admin,
            attendre_carte=self.attendre_carte,
        )

        print("Lecteur RFID pret. Approchez une carte !")

    def afficher_carte(self, uid: list[int]):
        print("\n####### Nouvelle carte detectee #######")
        print(f"UID  : {uid}")
        print("****************************************")

    def _verifier_carte(self, uid: list[int]):
        est_autorisee, nom, message, _, _ = self.gestion_csv.verifier_carte(uid)
        if est_autorisee:
            return True, nom, "Accepte"
        else:
            return False, nom, message

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
        if not os.path.exists(fichier_pass):
            return {}
        try:
            with open(fichier_pass, "r", encoding="utf-8") as f:
                data = json.load(f)
            questions = {}
            for entry in data.get("pass", []):
                uid = entry.get("uid")
                if uid:
                    questions[uid] = {
                        "nom": entry.get("nom", "Admin"),
                        "question": entry.get("question", ""),
                        "reponse": entry.get("reponse", ""),
                    }
            return questions
        except Exception:
            return {}

    def simulateActionCost(self, card_uid: list[int], credit_cost: int = 1):
        print(f"Decrementation de {credit_cost} credit(s)…")
        success, remaining = self.card_service.decrement(card_uid, credit_cost)
    
        if success:
            return remaining # ajout pour mettre le reste dans le csv directement
            print(f"{credit_cost} credit utilise - il reste {remaining} credit(s).")
        else:
            print(f"Decrementation impossible - credit restant : {remaining}.")

    def lancer(self):
        try:
            while True:
                try:
                    print("En attente d'une carte...")
                    if self.ecran:
                        self.ecran.accueil()

                    uid_carte = self.attendre_carte(message=None)

                    temps_actuel = time.time()
                    uid_string = "-".join(str(octet) for octet in uid_carte)
                    est_autorisee, nom, statut = self._verifier_carte(uid_string)
                    date = time.strftime("%Y-%m-%d %H:%M:%S")

                    # MQTT
                    self.mqtt_publisher.publish(date, uid_carte)

                    self.afficher_carte(uid_carte)
                    print(f"Nom: {nom}")
                    print(f"Statut: {statut}")

                    # Anti-double-scan protection
                    temps_ecoule = temps_actuel - self.dernier_temps
                    if uid_string == self.derniere_carte:
                        if temps_ecoule < 5:
                            print("Carte deja lue et debitee. Attendre 5 secondes pour une nouvelle lecture.")
                            time.sleep(0.5)
                            continue
                    else:
                        if temps_ecoule < self.delai_lecture:
                            time.sleep(0.2)
                            continue

                    print("\n===== Carte detectee =====")
                    print("UID :", uid_carte)

                    # --- Verification ---
                    carte_ok, nom_utilisateur = identifier_carte(uid_carte)
                    if carte_ok:
                        self.acces.carte_acceptee(nom=nom_utilisateur)
                    else:
                        self.acces.carte_refusee()

                    if not est_autorisee:
                        print(f"Carte non autorisée : {uid_string}")
                        # Log blocked access
                        self.mqtt_publisher.publish(date, uid_carte)
                        self.journal.enregistrer(date, uid_carte, nom, statut)
                    else:
                        # --- ADMIN CARD ---
                        if nom.lower() == "admin":
                            admin_ok = self.admin_interface.autoriser_admin(uid_string)

                            if admin_ok:
                                # Log admin access before opening menu
                                self.mqtt_publisher.publish(date, uid_carte)
                                self.journal.enregistrer(date, uid_carte, nom, statut)

                                self.admin_interface.run(uid_carte)

                        # --- NORMAL CARD : decrement credits ---    
                        else:
                            try:
                                self.simulateActionCost(uid_carte, 1)

                                
                                #succes_decrementation, nouveaux_credits = self.simulateActionCost(uid_carte, 1)
                                #if succes_decrementation : 
                                #    self.gestion_csv.mettre_a_jour_credits(uid_string, nouveaux_credits)
                                #self.gestion_csv.decrementer_un_credit(uid_string)
                            except Exception as err:
                                print(f"[ERREUR ECRITURE CREDITS] {err}")
                            finally:
                                # Log normal card access regardless of success/failure
                                self.mqtt_publisher.publish(date, uid_carte)
                                self.journal.enregistrer(date, uid_carte, nom, statut)

                    self.derniere_carte = uid_string
                    self.dernier_temps = temps_actuel

                except Exception as loop_error:
                    # Catch ANY error inside loop but keep system running
                    print(f"[ERREUR NON-GEREE] {loop_error}")
                    time.sleep(0.5)  # small delay for stability
        finally:
            # Cleanup
            self.feedback.cleanup()
            self.rfid.cleanup()

            self.mqtt_publisher.close()

            print(" Nettoyage termine.")
