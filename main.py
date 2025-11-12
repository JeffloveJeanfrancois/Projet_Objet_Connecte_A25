from lecteur_rfid import LecteurRFID  # importe la classe simplifiée

def main():
    # Création du lecteur RFID
    lecteur = LecteurRFID(
        broche_buzzer=33,   
        delai_lecture=2,
        broker="192.168.40.122",  
        port=1883,
        sujet_log="LecteurRFID/log"    
    )

    # Lance la détection en boucle
    lecteur.lancer()


if __name__ == "__main__":
    main()
