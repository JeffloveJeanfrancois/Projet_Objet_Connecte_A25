from RFIDController import RFIDController
import os

# --- CONFIGURATION AZURE PUBLISHER ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CERTFILE = os.path.join(BASE_DIR, "certs", "client-publisher.pem")
KEYFILE  = os.path.join(BASE_DIR, "certs", "client-publisher.key")

AZURE_BROKER = "broker-mqtt.canadaeast-1.ts.eventgrid.azure.net"
AZURE_PORT = 8883
AZURE_USERNAME = "client-publisher"
AZURE_TOPIC_BASE = "LecteurRFID/logs"


def main():
    # Création du lecteur RFID
    lecteur = RFIDController(
        broche_buzzer=33,   
        delai_lecture=2,
        
        # --- CONFIGURATION AZURE ---
        broker=AZURE_BROKER,  
        port=AZURE_PORT,
        sujet_log=AZURE_TOPIC_BASE,
        mqtt_username=AZURE_USERNAME,
        mqtt_certfile=CERTFILE,
        mqtt_keyfile=KEYFILE,
        # ---------------------------
        
        fichier_cartes="cartes_autorisees.csv"  
    )

    # Lance la détection en boucle
    lecteur.lancer()


if __name__ == "__main__":
    main()
