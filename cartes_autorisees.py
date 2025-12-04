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
                        
                        est_actif = str(ligne.get("Actif")).strip().lower() == "true"
                        nom = ligne.get("Nom", "Inconnu")
                        
                        try:
                            credits = int(ligne.get("Credits", 0))
                        except:
                            credits = 0

                        try:
                            id_interne = int(ligne.get("Id", 0))
                        except:
                            id_interne = 0

                        message = "Accepté" if est_actif else "Refusé (Désactivé)"
                        
                        return est_actif, nom, message, credits, id_interne
            
            return False, "Non renseigné", "Refusé - Carte inconnue", 0, 0

        except Exception as e:
            print(f"[ERREUR VERIFICATION] {e}")
            return False, "Erreur", "Erreur fichier", 0, 0

    def ajouter_ou_modifier_carte(self, uid, nom, actif, credits):
        toutes_les_lignes = self._lire_toutes_les_donnees()
        
        carte_trouvee = False
        max_id = 0
        id_final = 0 

        for ligne in toutes_les_lignes:
            try:
                id_courant = int(ligne.get("Id", 0))
                if id_courant > max_id:
                    max_id = id_courant
            except:
                pass
            
            # Si c'est la carte qu'on modifie
            if ligne.get("UID") == uid:
                ligne["Nom"] = nom
                ligne["Actif"] = str(actif)
                ligne["Credits"] = str(credits)
                
                id_final = id_courant 
                carte_trouvee = True

        if not carte_trouvee:
            # Nouvelle carte
            id_final = max_id + 1
            nouvelle_ligne = {
                "UID": uid,
                "Nom": nom,
                "Actif": str(actif),
                "Credits": str(credits),
                "Id": str(id_final) 
            }
            toutes_les_lignes.append(nouvelle_ligne)
            print(f"[INFO] Nouvelle carte ajoutée avec ID : {id_final}")
        
        succes = self._sauvegarder_donnees(toutes_les_lignes)
        
        if succes:
            print(f"[SUCCES] Carte {nom} enregistrée (ID: {id_final}, Credits: {credits})")
            return True, int(id_final)
        else:
            return False, 0