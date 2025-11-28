import csv
from datetime import datetime
import json # Import ajouté

FICHIER_CARTES = "cartes_autorisees.json" # Changé de .csv à .json
FICHIER_HISTORIQUE = "historique_acces.csv"


def charger_cartes_autorisees():
    cartes = {}
    try:
        with open(FICHIER_CARTES, 'r') as f:
            data = json.load(f)
            # Extrait les UIDs et les informations associées
            for item in data.get('cartes', []):
                uid = item.get('uid')
                if uid:
                    cartes[uid] = item
        return cartes
    except FileNotFoundError:
        print(f"Erreur: Le fichier des cartes autorisees {FICHIER_CARTES} est introuvable.")
        return {}
    except json.JSONDecodeError:
        print(f"Erreur: Le fichier {FICHIER_CARTES} n'est pas un JSON valide.")
        return {}


def enregistrer_historique(carte_id, nom, statut):
    date_heure = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(FICHIER_HISTORIQUE, "a", newline='') as f:
        writer = csv.writer(f)
        # Note: Dans un système complet, la ligne d'en-tête devrait être gérée.
        writer.writerow([carte_id, nom, date_heure, statut])


def identifier_carte(uid):
    carte_id = "-".join(str(o) for o in uid)

    cartes = charger_cartes_autorisees()

    if carte_id in cartes:
        carte_info = cartes[carte_id]
        nom = carte_info.get("nom", "Inconnu")
        actif = carte_info.get("actif", False)

        if actif:
            print(f"Bienvenue {nom}")
            enregistrer_historique(carte_id, nom, "accepte")
            return True, nom
        else:
            print(f"Accès refusé – Carte désactivée pour {nom}")
            enregistrer_historique(carte_id, nom, "refuse (désactivée)")
            return False, nom

    else:
        print("Acces refuse – Carte inconnue")
        enregistrer_historique(carte_id, "inconnu", "refuse")
        return False, "Inconnu"