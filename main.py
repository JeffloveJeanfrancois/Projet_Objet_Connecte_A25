from lecteur_rfid import LecteurRFID  # importe la classe simplifiée
   #from typing import dict



def main():
    # Création du lecteur RFID
    lecteur = LecteurRFID(
        broche_buzzer=33,   
        delai_lecture=2,
        broker="10.4.1.164",  
        port=1883,
        sujet_log="LecteurRFID/log",
        fichier_cartes_csv="cartes_autorisees.csv"
    )

    # Lance la détection en boucle
    lecteur.lancer()


if __name__ == "__main__":
    main()
