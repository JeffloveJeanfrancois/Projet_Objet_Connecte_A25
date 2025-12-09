import csv
import os
from datetime import datetime 
from tabulate import tabulate 
class GestionCartesCSV:
    def __init__(self, nom_fichier="cartes_autorisees.csv"):
        self.nom_fichier = nom_fichier
        self.colonnes = ["UID", "Nom", "Actif", "Credits", "Id", "Expiration", "Debut", "Fin","Jours"]        
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
        # On lit tout pour pouvoir modifier si expiré
        toutes_les_lignes = self._lire_toutes_les_donnees()
        carte_trouvee = False
        ligne_modifiee = None
        acces_horaire = False

        nom = "Inconnu"
        message = "Refusé - Carte inconnue"
        credits = "0"
        id_interne = ""

        for ligne in toutes_les_lignes:
            if ligne.get("UID") == uid_recherche:
                carte_trouvee = True
                nom = ligne.get("Nom", "Inconnu")
                credits = ligne.get("Credits", "0")
                id_interne = ligne.get("Id", "")
                expiration_str = ligne.get("Expiration", "")
                
                est_actif = str(ligne.get("Actif")).strip().lower() == "true"
                
                # expiration
                if est_actif and expiration_str:
                    try:
                        date_exp = datetime.strptime(expiration_str, "%Y-%m-%d")
                        if datetime.now() > date_exp:
                            print(f"[AUTO] Carte {nom} expirée le {expiration_str}. Désactivation...")
                            ligne["Actif"] = "False" # si expire on modifie
                            est_actif = False
                            ligne_modifiee = True
                            message = f"Refusé (Expiré le {expiration_str})"
                    except ValueError:
                        pass
                # jours de la semaine
                jours_autorises = ligne.get("Jours", "")
                if est_actif and jours_autorises:
                    #0=lundi/6=dimanche
                    jour_actuel = str(datetime.now().weekday()) 
                    liste_jours = jours_autorises.split("-") 
                    
                    if jour_actuel not in liste_jours:
                        est_actif = False
                        jours_noms = ["Lun", "Mar", "Mer", "Jeu", "Ven", "Sam", "Dim"]
                        nom_jour = jours_noms[int(jour_actuel)]
                        message = f"Refusé pour la journée du {nom_jour}"

                heure_debut_str = ligne.get("Debut", "")
                heure_fin_str = ligne.get("Fin", "")

                if est_actif  and heure_debut_str and heure_fin_str:
                    try:
                        maintenant = datetime.now().time()
                        debut = datetime.strptime(heure_debut_str, "%H:%M").time()
                        fin = datetime.strptime(heure_fin_str, "%H:%M").time()
                
                        if debut <= fin:
                            # Cas entre 08:00 et 16:00
                            if debut <= maintenant <= fin:
                                acces_horaire = True
                        else:
                        # Cas entre 22:00 et 06:00
                            if maintenant >= debut or maintenant <= fin:
                                acces_horaire = True

                        if not acces_horaire:
                            message = f"Refusé (Horaire {heure_debut_str}-{heure_fin_str})"
                            est_actif = False 
            
                    except ValueError:
                        pass
                if not message.startswith("Refusé"): 
                    message = "Accepté" if est_actif else "Refusé (Désactivé)"
                break
        
        if carte_trouvee and ligne_modifiee:
            self._sauvegarder_donnees(toutes_les_lignes)

        if carte_trouvee:
            return est_actif, nom, message, credits, id_interne
        else:
            return False, "Non renseigne", "Refusé - Carte inconnue", "0", ""

    def ajouter_ou_modifier_carte(self, uid, nom, actif, credits,expiration="",debut="", fin="",jours=""):
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
                ligne["Expiration"] = expiration
                ligne["Debut"] = debut 
                ligne["Fin"] = fin
                ligne["Jours"] = jours
                
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
                "Id": id_final,
                "Expiration": expiration,
                "Debut": debut, 
                "Fin": fin,
                "Jours": jours
                
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
    
    def supprimer_carte(self, uid):
        toutes_les_lignes = self._lire_toutes_les_donnees()
        
        lignes_restantes = [ligne for ligne in toutes_les_lignes if ligne.get("UID") != uid]

        if len(lignes_restantes) < len(toutes_les_lignes):
            succes = self._sauvegarder_donnees(lignes_restantes)
            if succes:
                print(f"[CSV] Carte {uid} supprimée de la base de données.")
                return True
        
        print(f"[CSV] Carte {uid} introuvable ou erreur de sauvegarde.")
        return False

    def afficher_toutes_les_cartes(self):
        lignes = self._lire_toutes_les_donnees()
        
        if not lignes:
            print("\nAUCUNE CARTE ENREGISTRÉE.\n")
            return

        table_data = []
        for ligne in lignes:
            actif_visuel = "Oui" if str(ligne.get("Actif")).lower() == "true" else "Non"
            
            jours = ligne.get("Jours", "")
            if not jours:
                jours_visuel = "Tous"
            else:
                jours_visuel = jours


            table_data.append([
                ligne.get("Id", "?"),
                ligne.get("Nom", "Inconnu"),
                ligne.get("Credits", "0"),
                actif_visuel,
                ligne.get("Expiration", "-"),
                f"{ligne.get('Debut','')} - {ligne.get('Fin','')}", 
                jours_visuel,
                ligne.get("UID", "")
            ])

        headers = ["ID", "Nom", "Crédits", "Actif","Expiration","Horaires","Jours", "UID "]
        
        print("\n" + "="*50)
        print(" LISTE DES UTILISATEURS")
        print("="*50)
        print(tabulate(table_data, headers=headers, tablefmt="fancy_grid"))
        print("\n")