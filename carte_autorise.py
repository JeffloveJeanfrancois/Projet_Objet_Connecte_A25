import csv
import os
import shutil
from tempfile import NamedTemporaryFile

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
                            return True, nom, "Accepté", credits, id_carte
                        else:
                            return False, nom, "Refusé - non autorisé", credits, id_carte

            # Si on sort de la boucle → carte non trouvée
            return False, "Non renseigné", "Refusé - Carte inconnue", "0", ""

        except Exception as e:
            print(f"[Erreur CSV] {e}")
            return False, "Erreur", "Erreur lecture CSV", "0", ""
        

    def verifier_carte(self, uid):
        try:
            with open(self.nom_fichier, 'r', encoding='utf-8') as f:
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

    def mettre_a_jour_infos(self, uid, nouveaux_credits, nouvel_id):
        """
        Met à jour les crédits et l'ID pour un UID donné dans le fichier CSV.
        Utilise un fichier temporaire pour éviter de corrompre le fichier principal.
        """
        fichier_temp = NamedTemporaryFile(mode='w', delete=False, newline='', encoding='utf-8')
        
        mise_a_jour_effectuee = False

        try:
            with open(self.nom_fichier, 'r', encoding='utf-8') as csv_original, fichier_temp:
                reader = csv.DictReader(csv_original)
                fieldnames = reader.fieldnames
                
                # On s'assure que les colonnes existent
                if "Credits" not in fieldnames: fieldnames.append("Credits")
                if "Id" not in fieldnames: fieldnames.append("Id")

                writer = csv.DictWriter(fichier_temp, fieldnames=fieldnames)
                writer.writeheader()

                for ligne in reader:
                    if ligne["UID"] == uid:
                        # On met à jour les valeurs pour cet UID
                        ligne["Credits"] = str(nouveaux_credits)
                        ligne["Id"] = str(nouvel_id)
                        mise_a_jour_effectuee = True
                    writer.writerow(ligne)
            
            # Remplacement du fichier original par le fichier temporaire
            shutil.move(fichier_temp.name, self.nom_fichier)
            
            if mise_a_jour_effectuee:
                print(f"[CSV] Mise à jour réussie pour UID {uid} : Credits={nouveaux_credits}, Id={nouvel_id}")
            else:
                print(f"[CSV] Attention : UID {uid} non trouvé, pas de mise à jour.")
                
        except Exception as e:
            print(f"[Erreur Mise à jour CSV] {e}")