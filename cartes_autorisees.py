import csv
import os

class GestionAcces:
    def __init__(self, nom_fichier="cartes_autorisees.csv"):
        self.nom_fichier = nom_fichier
        self.colonnes_officielles = ["UID", "Nom", "Actif", "Credits", "Id"]
        self.creer_fichier_si_absent()

    def creer_fichier_si_absent(self):
        if not os.path.exists(self.nom_fichier) or os.path.getsize(self.nom_fichier) == 0:
            print(f"Initialisation du fichier {self.nom_fichier}...")
            # Données de base
            donnees_initiales = [
                {"UID": "111-111-111-111-111", "Nom": "Yan LeKerreq", "Actif": "True", "Credits": "0", "Id": "1"},
                {"UID": "111-111-111-111-113", "Nom": "Michel Sansfaçon", "Actif": "False", "Credits": "0", "Id": "2"},
                {"UID": "250-152-169-174-101", "Nom": "Admin", "Actif": "True", "Credits": "999", "Id": "0"}
            ]
            try:
                with open(self.nom_fichier, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=self.colonnes_officielles)
                    writer.writeheader()
                    writer.writerows(donnees_initiales)
                print(f"Fichier {self.nom_fichier} généré avec succès.")
            except Exception as e:
                print(f"[ERREUR CRITIQUE] Impossible de créer le fichier CSV : {e}")

    def verifier_carte(self, uid):
        try:
            if not os.path.exists(self.nom_fichier):
                self.creer_fichier_si_absent()

            with open(self.nom_fichier, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for ligne in reader:
                    if ligne.get("UID") == uid:
                        est_actif = str(ligne.get("Actif", "False")).strip().lower() == "true"
                        nom = ligne.get("Nom", "Inconnu")
                        credits = ligne.get("Credits", "0")
                        id_carte = ligne.get("Id", "")
                        return est_actif, nom, "Accepté" if est_actif else "Refusé", credits, id_carte

            return False, "Non renseigné", "Refusé - Carte inconnue", "0", ""
        except Exception as e:
            return False, "Erreur", f"Erreur lecture: {e}", "0", ""

    def ajouter_ou_modifier_carte(self, uid, nom, actif, credits):
        """
        Renvoie maintenant (True, id_final) si succès, ou (False, None) si échec.
        """
        lignes = []
        max_id = 0
        trouve = False
        str_actif = str(actif)
        str_credits = str(credits)
        id_final = None # Variable pour stocker l'ID qu'on va utiliser

        # 1. LECTURE COMPLETE
        if os.path.exists(self.nom_fichier):
            try:
                with open(self.nom_fichier, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        clean_row = {k: row.get(k, "") for k in self.colonnes_officielles}
                        
                        # Calcul ID Max
                        if clean_row["Id"].isdigit():
                            val_id = int(clean_row["Id"])
                            if val_id > max_id:
                                max_id = val_id
                        
                        lignes.append(clean_row)
            except Exception as e:
                print(f"[Attention] Erreur lecture : {e}")
                lignes = []

        # 2. MODIFICATION OU AJOUT
        for ligne in lignes:
            if ligne["UID"] == uid:
                ligne["Nom"] = nom
                ligne["Actif"] = str_actif
                ligne["Credits"] = str_credits
                
                # SI L'ID EST VIDE (Ancienne carte), ON LUI EN GENERE UN
                if not ligne["Id"]:
                    max_id += 1
                    ligne["Id"] = str(max_id)
                    print(f"[AUTO-ID] ID généré pour carte existante : {ligne['Id']}")
                
                id_final = ligne["Id"]
                trouve = True
                break
        
        if not trouve:
            # NOUVELLE CARTE
            max_id += 1
            id_final = str(max_id)
            nouvelle_ligne = {
                "UID": uid,
                "Nom": nom,
                "Actif": str_actif,
                "Credits": str_credits,
                "Id": id_final
            }
            lignes.append(nouvelle_ligne)
            print(f"[AUTO-ID] Nouvel ID généré : {id_final}")

        # 3. ÉCRITURE
        try:
            with open(self.nom_fichier, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.colonnes_officielles)
                writer.writeheader()
                writer.writerows(lignes)
            
            try:
                os.chmod(self.nom_fichier, 0o666)
            except:
                pass
                
            print(f"[CSV] Sauvegarde OK : {nom} (ID: {id_final}, Crédits: {credits})")
            return True, id_final 
            
        except Exception as e:
            print(f"[Erreur Écriture CSV] {e}")
            return False, None