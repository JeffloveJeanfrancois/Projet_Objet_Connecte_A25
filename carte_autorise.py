import csv
import os
import shutil
from tempfile import NamedTemporaryFile

class GestionAcces:
    def __init__(self, nom_fichier="cartes_autorisees.csv"):
        self.nom_fichier = nom_fichier
        self.creer_fichier_si_absent()

    def creer_fichier_si_absent(self):

        if not os.path.exists(self.nom_fichier):
            print(f"Création du fichier {self.nom_fichier} avec les données de base...")
            
            # Les données de base (anciennement dans ton JSON)
            donnees_initiales = [
                {"UID": "111-111-111-111-111", "Nom": "Yan LeKerreq", "Actif": "True", "Credits": "0", "Id": ""},
                {"UID": "212-235-89-42-76", "Nom": "Claire Obscur", "Actif": "True", "Credits": "0", "Id": ""},
                {"UID": "111-111-111-111-113", "Nom": "Michel Sansfaçon", "Actif": "False", "Credits": "0", "Id": ""},
                {"UID": "250-152-169-174-101", "Nom": "Admin", "Actif": "True", "Credits": "999", "Id": "ADMIN01"}
            ]

            entetes = ["UID", "Nom", "Actif", "Credits", "Id"]

            try:
                with open(self.nom_fichier, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=entetes)
                    writer.writeheader()
                    writer.writerows(donnees_initiales)
                print(f"Fichier {self.nom_fichier} créé avec succès.")
            except Exception as e:
                print(f"[ERREUR] Impossible de créer le fichier CSV : {e}")

    def verifier_carte(self, uid):
        try:
            with open(self.nom_fichier, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for ligne in reader:
                    if ligne["UID"] == uid:
                        # CHANGEMENT ICI : On lit la colonne "Actif" au lieu de "Autorise"
                        est_actif = ligne["Actif"].strip().lower() == "true"
                        nom = ligne["Nom"]
                        
                        # On récupère les crédits et l'ID (valeur par défaut "0" et "")
                        credits = ligne.get("Credits", "0")
                        id_carte = ligne.get("Id", "")

                        if est_actif:
                            return True, nom, "Accepté", credits, id_carte
                        else:
                            return False, nom, "Refusé - Compte inactif", credits, id_carte

            # Si on sort de la boucle → carte non trouvée
            return False, "Non renseigné", "Refusé - Carte inconnue", "0", ""

        except Exception as e:
            print(f"[Erreur CSV] {e}")
            return False, "Erreur", "Erreur lecture CSV", "0", ""

    def mettre_a_jour_infos(self, uid, nouveaux_credits, nouvel_id):

        fichier_temp = NamedTemporaryFile(mode='w', delete=False, newline='', encoding='utf-8')
        
        mise_a_jour_effectuee = False

        try:
            with open(self.nom_fichier, 'r', encoding='utf-8') as csv_original, fichier_temp:
                reader = csv.DictReader(csv_original)
                fieldnames = reader.fieldnames
                
                # Sécurité : on s'assure que les colonnes existent
                if "Credits" not in fieldnames: fieldnames.append("Credits")
                if "Id" not in fieldnames: fieldnames.append("Id")

                writer = csv.DictWriter(fichier_temp, fieldnames=fieldnames)
                writer.writeheader()

                for ligne in reader:
                    if ligne["UID"] == uid:
                        ligne["Credits"] = str(nouveaux_credits)
                        ligne["Id"] = str(nouvel_id)
                        mise_a_jour_effectuee = True
                    writer.writerow(ligne)
            
            shutil.move(fichier_temp.name, self.nom_fichier)
            
            if mise_a_jour_effectuee:
                print(f"[CSV] Mise à jour réussie pour UID {uid}")
            else:
                os.remove(fichier_temp.name) # Nettoyage si échec
                print(f"[CSV] Attention : UID {uid} non trouvé.")
                
        except Exception as e:
            print(f"[Erreur Mise à jour CSV] {e}")
    

    def ajouter_ou_modifier_carte(self, uid, nom, actif):
        """
        Ajoute une nouvelle carte ou met à jour le nom/statut d'une carte existante dans le CSV.
        """
        fichier_temp = NamedTemporaryFile(mode='w', delete=False, newline='', encoding='utf-8')
        trouve = False
        
        # Convertir le booléen en string pour le CSV
        str_actif = str(actif) # "True" ou "False"

        try:
            with open(self.nom_fichier, 'r', encoding='utf-8') as csv_original, fichier_temp:
                reader = csv.DictReader(csv_original)
                fieldnames = reader.fieldnames
                
                writer = csv.DictWriter(fichier_temp, fieldnames=fieldnames)
                writer.writeheader()

                for ligne in reader:
                    if ligne["UID"] == uid:
                        # Mise à jour de la carte existante
                        ligne["Nom"] = nom
                        ligne["Actif"] = str_actif
                        trouve = True
                    writer.writerow(ligne)
                
                # Si la carte n'existait pas, on l'ajoute à la fin
                if not trouve:
                    writer.writerow({
                        "UID": uid,
                        "Nom": nom,
                        "Actif": str_actif,
                        "Credits": "0",
                        "Id": ""
                    })

            shutil.move(fichier_temp.name, self.nom_fichier)
            print(f"[CSV] Carte {uid} sauvegardée : {nom} (Actif: {str_actif})")
            return True

        except Exception as e:
            print(f"[Erreur Écriture CSV] {e}")
            if os.path.exists(fichier_temp.name):
                os.remove(fichier_temp.name)
            return False