import time
from lecteur.rfid_driver import RfidDriver
from lecteur.hardware import LedBuzzer
from carte.gestion_cartes import GestionCartes
#from carte.questions_admin import QuestionsAdmin
from logs.mqtt_logger import MqttLogger
from logs.historique import HistoriqueDesAcces
from admin.interface_admin import InterfaceAdmin
#from carte.gestion_cartes import GestionCartes


class LecteurRFID:

    def __init__(self):
        self.rfid = RfidDriver()
        self.hw = LedBuzzer()
        self.cartes = GestionCartes()
        #self.questions_admin = QuestionsAdmin()
        self.mqtt = MqttLogger()
        self.historique = HistoriqueDesAcces()
        #self.interface_admin = InterfaceAdmin()
        self.interface_admin = InterfaceAdmin(self.cartes)
        #self.interface_admin = InterfaceAdmin(self.cartes, self.questions_admin)


        self.derniere_carte = None
        self.dernier_temps = 0
        self.delai_lecture = 2

        print("Lecteur RFID prêt. Approchez une carte !")

    def lancer(self):
        while True:
            uid = self.rfid.detecter_uid()
            if uid is None:
                time.sleep(0.1)
                continue

            now = time.time()
            if uid == self.derniere_carte and (now - self.dernier_temps) < self.delai_lecture:
                print("Carte déjà passée récemment. Pause...")
                continue

            type_carte = "RFID"
            date = time.strftime("%Y-%m-%d %H:%M:%S")

            est_autorisee, nom, statut = self.cartes.verifier(uid)

            if est_autorisee:
                self.hw.ok()
            else:
                self.hw.erreur()

            # ADMIN ?
            if est_autorisee and nom.lower() == "admin":
                #self.interface_admin.lancer(uid, self.questions_admin)
                self.interface_admin.lancer(uid)

            # logs
            self.mqtt.envoyer(date, type_carte, uid)
            self.historique.enregistrer(date, type_carte, uid, nom, statut)

            self.derniere_carte = uid
            self.dernier_temps = now
