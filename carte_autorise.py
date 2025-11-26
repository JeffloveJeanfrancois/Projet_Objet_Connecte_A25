import csv
import os

class GestionAcces:
    def __init__(self, nom_fichier="cartes_autorisees.csv"):
        self.nom_fichier = nom_fichier
        self.creer_fichier_si_absent()

    def creer_fichier_si_absent(self):
        #Crée le fichier CSV s'il n'existe pas 
        if not os.path.exists(self.nom_fichier):
            with open(self.nom_fichier, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["UID", "Credits"])
            print(f"[Zakaria] Fichier {self.nom_fichier} créé.")

    def verifier_et_debiter(self, uid_cible):
        """
        Cherche l'UID, vérifie s'il a des crédits, enlève 1 crédit et sauvegarde.
        Retourne : (True/False, nombre_credits_restants)
        """
        lignes = []
        acces_autorise = False
        solde = 0
        
        # Lire tout le fichier
        try:
            with open(self.nom_fichier, 'r') as f:
                reader = csv.reader(f)
                lignes = list(reader)
        except FileNotFoundError:
            return False, 0

        # Parcourir et modifier
        carte_trouvee = False
        for ligne in lignes:
            # ligne[0] = UID, ligne[1] = Credits
            if len(ligne) >= 2 and ligne[0] == uid_cible:
                carte_trouvee = True
                try:
                    credits = int(ligne[1])
                    if credits > 0:
                        credits = credits - 1  # On décrémente
                        ligne[1] = str(credits) # On met à jour la ligne
                        acces_autorise = True
                        solde = credits
                    else:
                        solde = 0 # Plus de crédit
                except ValueError:
                    pass # Erreur de conversion chiffre
                break #on sort de la boucle

        # Sauvegarder SI on a modifié quelque chose
        if acces_autorise:
            with open(self.nom_fichier, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(lignes)
        
        return acces_autorise, solde