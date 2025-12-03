#!/usr/bin/env python3

# Script de test pour le lecteur RFID sans MQTT.

from RFID_controller import RFIDController


def main():
    print("=" * 60)
    print("TEST DU LECTEUR RFID (SANS MQTT)")
    print("=" * 60)
    print("\nCe script teste le lecteur RFID sans connexion MQTT.")
    print("Les cartes seront detectees et enregistrees dans le journal CSV.")
    
    # Creation du lecteur RFID sans MQTT
    lecteur = RFIDController(
        broche_buzzer=33,   
        delai_lecture=2,
        nom_fichier="journal_rfid.csv",
        fichier_cartes="cartes_autorisees.json",
        utiliser_mqtt=False  # Desactive MQTT
    )

    # Lance la detection en boucle
    try:
        lecteur.lancer()
    except KeyboardInterrupt:
        print("\n\nTest arrete par l'utilisateur.")
    except Exception as e:
        print(f"\n[ERREUR] Une erreur s'est produite: {e}")
    finally:
        print("\nTest termine.")


if __name__ == "__main__":
    main()

