from lecteur_rfid import LecteurRFID  # importe la classe simplifiée

def main():
    # Création du lecteur RFID
    lecteur = LecteurRFID(
        broche_buzzer=33,   
        delai_lecture=2    
    )

    # Lance la détection en boucle
    lecteur.lancer()


if __name__ == "__main__":
    main()
