import csv
import os

class GestionAcces:
    def __init__(self, nom_fichier="cartes_autorisees.csv"):
        self.nom_fichier = nom_fichier
        self.creer_fichier_si_absent()

    def creer_fichier_si_absent(self):
        # Crée le fichier CSV s'il n'existe pas avec les nouvelles colonnes
        if not os.path.exists(self.nom_fichier):
            with open(self.nom_fichier, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # Ajout des colonnes Id et Credits
                writer.writerow(["UID", "Nom", "Autorise", "Credits", "Id"])
            print(f"Fichier {self.nom_fichier} créé.")

    def verifier_carte(self, uid):
        try:
            with open(self.nom_fichier, 'r') as f:
                reader = csv.DictReader(f)

                for ligne in reader:
                    if ligne["UID"] == uid:
                        autorise = ligne["Autorise"].strip().lower() == "true"
                        nom = ligne["Nom"]
                        # On récupère les crédits et l'ID (avec une valeur par défaut si vide)
                        credits = ligne.get("Credits", "0")
                        id_carte = ligne.get("Id", "")

                        if autorise:
                            # On retourne True, Nom, Message, Credits, Id
                            return True, nom, "Accepté", credits, id_carte
                        else:
                            return False, nom, "Refusé - non autorisé", credits, id_carte

            # Si on sort de la boucle → carte non trouvée
            return False, "Non renseigné", "Refusé - Carte inconnue", "0", ""

        except Exception as e:
            print(f"[Erreur CSV] {e}")
            return False, "Erreur", "Erreur lecture CSV", "0", ""