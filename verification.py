import csv
from datetime import datetime

FICHIER_CARTES = "cartes_autorisees.csv"
FICHIER_HISTORIQUE = "historique_acces.csv"


def charger_cartes_autorisees():
    cartes = {}
    with open(FICHIER_CARTES, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cartes[row["carte_id"]] = row
    return cartes


def enregistrer_historique(carte_id, nom, statut):
    date_heure = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(FICHIER_HISTORIQUE, "a", newline='') as f:
        writer = csv.writer(f)
        writer.writerow([carte_id, nom, date_heure, statut])


def identifier_carte(uid):
    carte_id = "-".join(str(o) for o in uid)

    cartes = charger_cartes_autorisees()

    if carte_id in cartes:
        nom = cartes[carte_id]["nom"]
        print(f"Bienvenue {nom}")
        enregistrer_historique(carte_id, nom, "accepte")
        return True

    else:
        print("Accès refusé – Carte inconnue")
        enregistrer_historique(carte_id, "inconnu", "refuse")
        return False
