import csv
import os

class GestionAcces:
    def __init__(self, nom_fichier="cartes_autorisees.csv"):
        self.nom_fichier = nom_fichier
        self.creer_fichier_si_absent()

    def creer_fichier_si_absent(self):
    # Crée le fichier CSV s'il n'existe pas 
        if not os.path.exists(self.nom_fichier):
            with open(self.nom_fichier, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["UID", "Nom", "Autorise"])
            print(f"Fichier {self.nom_fichier} créé.")


    def verifier_carte(self, uid):
        try:
            with open(self.fichier_cartes_csv, 'r') as f:
                reader = csv.DictReader(f)

                for ligne in reader:
                    if ligne["UID"] == uid:
                        autorise = ligne["Autorise"].strip().lower() == "true"
                        nom = ligne["Nom"]

                        if autorise :
                            return True, nom, "Accepté"
                        else:
                            return False, nom, "Refusé - non autorisé"

            # Si on sort de la boucle → carte non trouvée
            return False, "Non renseigné", "Refusé - Carte inconnue"

        except Exception as e:
            print(f"[Erreur CSV] {e}")
            return False, "Erreur", "Erreur lecture CSV"