import csv
import os

class GestionCartesCSV:

    def __init__(self, nom_fichier="cartes_autorisees.csv"):
        self.nom_fichier = nom_fichier
        self.colonnes = ["UID", "Nom", "Actif", "Credits", "Id"]
        self._initialiser_fichier()

    def _initialiser_fichier(self):
        if not os.path.exists(self.nom_fichier):
            print(f"Création du fichier {self.nom_fichier}...")
            try:
                with open(self.nom_fichier, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.DictWriter(file, fieldnames=self.colonnes)
                    writer.writeheader()
                print("[CSV] Fichier initialisé avec succès.")
            except Exception as e:
                print(f"[ERREUR CRITIQUE] Impossible de créer le CSV : {e}")

    def _lire_toutes_les_donnees(self):
        donnees = []
        if os.path.exists(self.nom_fichier):
            try:
                with open(self.nom_fichier, 'r', encoding='utf-8') as file:
                    reader = csv.DictReader(file)
                    for ligne in reader:
                        donnees.append(ligne)
            except Exception as e:
                print(f"[ERREUR LECTURE] {e}")
        return donnees

    def _sauvegarder_donnees(self, lignes):
        #ecrase le fichier CSV avec la nouvelle liste de données fournie.
        try:
            with open(self.nom_fichier, 'w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=self.colonnes)
                writer.writeheader()
                writer.writerows(lignes)
            return True
        except Exception as e:
            print(f"[ERREUR ECRITURE] Impossible de sauvegarder : {e}")
            return False

    def verifier_carte(self, uid_recherche):
        try:
            with open(self.nom_fichier, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for ligne in reader:
                    if ligne.get("UID") == uid_recherche:
                        
                        # Conversion  des données 
                        est_actif = str(ligne.get("Actif")).strip().lower() == "true"
                        nom = ligne.get("Nom", "Inconnu")
                        credits = ligne.get("Credits", "0")
                        id_interne = ligne.get("Id", "")

                        message = "Accepté" if est_actif else "Refusé (Désactivé)"
                        
                        return est_actif, nom, message, credits, id_interne
            return False, "Non renseigne", "Refusé - Carte inconnue", "0", ""

        except Exception as e:
            print(f"[ERREUR VERIFICATION] {e}")
            return False, "Erreur", "Erreur fichier", "0", ""

    def ajouter_ou_modifier_carte(self, uid, nom, actif, credits):
        #ajoute une nouvelle carte ou met à jour une existante.
        toutes_les_lignes = self._lire_toutes_les_donnees() #charge les donnes en memoire
        
        carte_trouvee = False
        max_id = 0
        id_final = None

        for ligne in toutes_les_lignes:
            # Gestion de l'id
            id_courant_str = ligne.get("Id", "0")
            if id_courant_str and id_courant_str.isdigit():
                id_val = int(id_courant_str)
                if id_val > max_id:
                    max_id = id_val
            
            # Vérification si c'est la carte qu'on veut modifier
            if ligne.get("UID") == uid:
                # C'est une mise à jour !
                ligne["Nom"] = nom
                ligne["Actif"] = str(actif)
                ligne["Credits"] = str(credits)
                
                # Si par hasard l'ancienne carte n'avait pas d'ID, on lui en donnera un plus tard
                if ligne.get("Id"):
                    id_final = ligne["Id"]
                
                carte_trouvee = True

        # 3. Logique d'attribution d'ID et d'Ajout
        if not carte_trouvee:
            # Cas : C'est une NOUVELLE carte
            nouvel_id = max_id + 1
            id_final = str(nouvel_id)
            
            nouvelle_ligne = {
                "UID": uid,
                "Nom": nom,
                "Actif": str(actif),
                "Credits": str(credits),
                "Id": id_final
            }
            toutes_les_lignes.append(nouvelle_ligne)
            print(f"[INFO] Nouvelle carte ajoutée avec ID : {id_final}")

        elif not id_final:
            # Cas : Carte existante mais qui n'avait pas d'ID (Ancien bug corrigé ici)
            nouvel_id = max_id + 1
            id_final = str(nouvel_id)
            # On doit retrouver la ligne pour lui mettre l'ID
            for ligne in toutes_les_lignes:
                if ligne["UID"] == uid:
                    ligne["Id"] = id_final
                    break
            print(f"[INFO] ID généré pour carte existante : {id_final}")

        # 4. Sauvegarde finale dans le fichier
        succes = self._sauvegarder_donnees(toutes_les_lignes)
        
        if succes:
            print(f"[SUCCES] Carte {nom} enregistrée (ID: {id_final}, Credits: {credits})")
            return True, id_final
        else:
            return False, None