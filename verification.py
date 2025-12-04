import csv
from datetime import datetime
import os

FICHIER_CARTES = "cartes_autorisees.csv"
FICHIER_HISTORIQUE = "historique_acces.csv"

def enregistrer_historique(carte_id, nom, statut):
    date_heure = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    fichier_existe = os.path.exists(FICHIER_HISTORIQUE)
    
    try:
        with open(FICHIER_HISTORIQUE, "a", newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not fichier_existe:
                writer.writerow(["UID", "Nom", "Date", "Statut"])
            writer.writerow([carte_id, nom, date_heure, statut])
    except Exception as e:
        print(f"Erreur écriture historique: {e}")

def identifier_carte(uid):
    carte_id = "-".join(str(o) for o in uid)
    nom_trouve = "Inconnu"
    est_actif = False
    carte_existe = False

    if os.path.exists(FICHIER_CARTES):
        try:
            with open(FICHIER_CARTES, mode='r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row["UID"] == carte_id:
                        carte_existe = True
                        nom_trouve = row["Nom"]
                        est_actif = str(row["Actif"]).strip().lower() == "true"
                        break
        except Exception as e:
            print(f"Erreur lors de la lecture du fichier cartes: {e}")
    else:
        print(f"[Attention] Le fichier {FICHIER_CARTES} n'existe pas encore.")

    if carte_existe:
        if est_actif:
            print(f"Bienvenue {nom_trouve}")
            enregistrer_historique(carte_id, nom_trouve, "accepte")
            return True, nom_trouve
        else:
            print(f"Accès refusé – Carte désactivée pour {nom_trouve}")
            enregistrer_historique(carte_id, nom_trouve, "refuse (desactivee)")
            return False, nom_trouve
    else:
        print("Acces refuse – Carte inconnue")
        enregistrer_historique(carte_id, "Inconnu", "refuse")
        return False, "Inconnu"