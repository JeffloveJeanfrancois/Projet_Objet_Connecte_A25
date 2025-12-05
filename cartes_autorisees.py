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
        #Charge  le contenu du fichier CSV dans une liste en mémoire
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
        #Prend une liste  en mémoire et écrase le fichier CSV avec.
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
                        credits = ligne.get("Credits", "0")
                        id_interne = ligne.get("Id", "")

                        message = "Accepté" if est_actif else "Refusé (Désactivé)"
                        
                        return est_actif, nom, message, credits, id_interne
            
            return False, "Non renseigne", "Refusé - Carte inconnue", "0", ""
        except Exception as e:
            print(f"[ERREUR VERIFICATION] {e}")
            return False, "Erreur", "Erreur fichier", "0", ""

    def ajouter_ou_modifier_carte(self, uid, nom, actif, credits):
        toutes_les_lignes = self._lire_toutes_les_donnees() 
        
        carte_trouvee = False
        max_id = 0      
        id_final = None 

        for ligne in toutes_les_lignes:
            id_courant_str = ligne.get("Id", "0")
            if id_courant_str and id_courant_str.isdigit():
                id_val = int(id_courant_str)
                if id_val > max_id:
                    max_id = id_val
            
            if ligne.get("UID") == uid:
                ligne["Nom"] = nom
                ligne["Actif"] = str(actif)
                ligne["Credits"] = str(credits)
                
                if ligne.get("Id"):
                    id_final = ligne["Id"]
                carte_trouvee = True

        # nouvelles cartes sans ID
        if not carte_trouvee:
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
            print(f" Nouvelle carte ajoutée avec ID : {id_final}")

        succes = self._sauvegarder_donnees(toutes_les_lignes)
        
        if succes:
            print(f"Carte {nom} enregistrée (ID: {id_final}, Credits: {credits})")
            return True, id_final
        else:
            return False, None

    def mettre_a_jour_credits(self, uid, nouveaux_credits):
        toutes_les_lignes = self._lire_toutes_les_donnees()
        
        maj_effectuee = False
        for ligne in toutes_les_lignes:
            if ligne.get("UID") == uid:
                ligne["Credits"] = str(nouveaux_credits)
                maj_effectuee = True
                break  
        if maj_effectuee:
            succes = self._sauvegarder_donnees(toutes_les_lignes)
            if succes:
                print(f"[CSV] Crédits mis à jour pour {uid}: {nouveaux_credits}")
                return True
        
        print(f"[ERREUR] Carte {uid} non trouvée ou échec sauvegarde")
        return False

    def decrementer_un_credit(self, uid):
        toutes_les_lignes = self._lire_toutes_les_donnees()
        modification_faite = False
        for ligne in toutes_les_lignes:
            if ligne.get("UID") == uid:
                try:
                    credits_actuels = int(ligne.get("Credits", "0"))
                except ValueError:
                    credits_actuels = 0

                if credits_actuels > 0:
                    ligne["Credits"] = str(credits_actuels - 1)
                    modification_faite = True
                    print(f"[CSV] Décrémentation pour {uid} : {credits_actuels} -> {credits_actuels - 1}")
                else:
                    print(f"[CSV] Échec : Solde à 0 pour {uid}")
                    return False
                
                break 
        
        if modification_faite:
            return self._sauvegarder_donnees(toutes_les_lignes)
        
        return False