import time
from rfid_lecteur import LecteurRFID
from card_manager import CardService
from card_utils import block_list_to_string, string_to_block_list, block_list_to_integer

class AdminInterface:
    def __init__(self, gestion_csv, mifare : LecteurRFID, questions_admin, attendre_carte):
        self.gestion_csv = gestion_csv
        self.mifare = mifare
        self.card_service = CardService(mifare)
        self.questions_admin = questions_admin
        self.attendre_carte = attendre_carte

    def autoriser_admin(self, uid_string: str):
        question_data = self.questions_admin.get(uid_string)
        if not question_data:
            return True

        print(f"[SECURITE] Question : {question_data['question']}")
        tentatives = 3
        while tentatives > 0:
            reponse = input("Reponse : ").strip()
            if reponse.lower() == question_data["reponse"].strip().lower():
                print("Acces admin autorise.")
                return True
            tentatives -= 1
            print(f"Reponse incorrecte. Essais restants: {tentatives}.")

        return False
    def ask_time(self, prompt: str, allow_empty=True):
        while True:
            rep = input(prompt).strip()
            if allow_empty and rep == "":
                return ""
            # verification du format HH:MM
            try:
                import datetime
                datetime.datetime.strptime(rep, "%H:%M")
                return rep
            except ValueError:
                print("Format invalide. Veuillez utiliser le format HH:MM (ex: 14:30).")
    def ask_yes_no(self, prompt: str):
        while True:
            rep = input(prompt).strip().lower()
            if rep in ("oui", "non"):
                return rep == "oui"
            print("Veuillez repondre par 'oui' ou 'non'.")

    def supprimer_un_utilisateur(self):
        print("\n--- Suppression d'utilisateur ---")
        uid_carte = self.attendre_carte("Veuillez approcher la carte a SUPPRIMER...")
        uid_str = "-".join(str(octet) for octet in uid_carte)

        existe, nom, _, _, _ = self.gestion_csv.verifier_carte(uid_str)

        if not existe:
            print(f"Erreur : La carte {uid_str} n'existe pas dans le système.")
            return

        print(f"Carte trouvée : {nom} (UID: {uid_str})")
        confirmation = self.ask_yes_no(f"Êtes-vous sûr de vouloir supprimer {nom} définitivement ? (oui/non) : ")

        if confirmation:
            if self.gestion_csv.supprimer_carte(uid_str):
                print("[SUCCES] Utilisateur supprimé.")
            else:
                print("[ERREUR] La suppression a échoué.")
        else:
            print("Suppression annulée.")
    def ask_int(self, prompt: str):
        while True:
            rep = input(prompt).strip()
            try:
                return int(rep)
            except ValueError:
                print("Veuillez entrer un nombre entier valide.")

    def ask_string(self, prompt: str, allow_empty=True):
        while True:
            rep = input(prompt).strip()
            if allow_empty or rep:
                return rep
            print("Veuillez entrer une valeur non vide.")

    def configurer_carte(self):
        uid_carte = self.attendre_carte("Veuillez approcher la carte a configurer...")
        uid_str = "-".join(str(octet) for octet in uid_carte)

        # Sécurité: carte admin interdite
        if uid_str in self.questions_admin:
            print("\033[91mVous n'etes pas autorise a configurer cette carte (carte admin).\033[0m")
            return
        
        # Vérifier si elle existe dans le CSV
        existe, nom_actuel, _, _, _ = self.gestion_csv.verifier_carte(uid_str)
        carte_trouvee = nom_actuel != "Non renseigne"

        nouveau_nom = nom_actuel if carte_trouvee else ""
        statut_actif = True
        nouveaux_credits = "0"
        expiration = ""
        debut = ""
        fin = ""

        # ------ Carte EXISTANTE ------
        if carte_trouvee:
            print(f"Carte existante : Nom = {nom_actuel}")

            ecraser = self.ask_yes_no("Ecraser ? (oui/non) : ")

            if ecraser:
                nouveau_nom = self.ask_string("Nom : ")
                statut_actif = self.ask_yes_no("Activer ? (oui/non) : ")
                nouveaux_credits = self.ask_int("Nouveau nombre de credits : ")
                expiration = input("Date d'expiration (AAAA-MM-JJ) ou Entrée pour aucune : ").strip()
                debut = self.ask_time("Heure de début (HH:MM) ou Entrée pour accès 24h/24 : ")
                fin = ""
                if debut:
                    fin = self.ask_time("Heure de fin (HH:MM) : ", allow_empty=False)
            else:
                print("Menu de lecture/ecriture")
                self.menu_configuration_blocs()
                return
            
        # ------ Nouvelle carte ------
        else:
            print("Nouvelle carte.")
            nouveau_nom = self.ask_string("Nom : ")
            statut_actif = self.ask_yes_no("Activer ? (oui/non) : ")
            nouveaux_credits = self.ask_int("Credits : ")
            expiration = input("Date d'expiration (AAAA-MM-JJ) ou Entrée pour aucune : ").strip()
            debut = self.ask_time("Heure de début (HH:MM) ou Entrée pour accès 24h/24 : ")
            fin = ""
            if debut:
                fin = self.ask_time("Heure de fin (HH:MM) : ", allow_empty=False) 

        # ------ Sauvegarde CSV ------
        succes, id_genere = self.gestion_csv.ajouter_ou_modifier_carte(
            uid_str, nouveau_nom, statut_actif, str(nouveaux_credits), expiration, debut, fin
        )

        # ------ Écriture RFID ------
        if succes and id_genere:
            print("\n[ECRITURE] Enregistrement sur la puce RFID...")
            print(f" -> Bloc 5 (Credits) : {nouveaux_credits}")
            
            # MODIFICATION ICI : On écrit l'ID (Bloc 4) SEULEMENT si c'est une nouvelle carte
            if not carte_trouvee:
                print(f" -> Bloc 4 (ID) : {id_genere}")
            else:
                print(f" -> Bloc 4 (ID) : Carte existante, on ne touche pas à l'ID.")

            uid_pour_ecriture = self.attendre_carte(
                message=">>> Veuillez RESCANNER la carte maintenant pour finaliser l'ecriture... <<<"
            )
            uid_str_verif = "-".join(str(octet) for octet in uid_pour_ecriture)
            if uid_str_verif != uid_str:
                print("[ERREUR] Ce n'est pas la même carte ! Annulation.")
            return

            # MODIFICATION ICI : Condition pour ne pas écrire si la carte existait déjà
            if not carte_trouvee:
                self.card_service.write_card_id(uid_pour_ecriture, str(id_genere))
            
            time.sleep(0.2)

            # On écrit toujours les crédits (Bloc 5), car ils changemt peuvent avoir changé
            uid_pour_ecriture = self.attendre_carte(message=None)
            self.card_service.write_counter(uid_pour_ecriture, nouveaux_credits)

            print("[SUCCES] Carte configurée !")

    def run(self, uid_admin: list[int]):
        print("\n=== Mode Admin active ===")

        while True:
            print("\nOptions :")
            print("1. Configurer une carte (Ajout/Modif + ecriture Blocs)")
            print("2. Supprimer un utilisateur") 
            print("3. Voir la liste des utilisateurs")
            print("4. Quitter")
            choix = input("Votre choix: ")

            if choix == "1":
                self.configurer_carte()
            elif choix == "2":
                self.supprimer_un_utilisateur()
            elif choix == "3" :
                self.gestion_csv.afficher_toutes_les_cartes() 
            elif choix == "4":
                print("Sortie du mode Admin.")
                break

            else:
                print("Choix invalide.")

    def menu_configuration_blocs(self):
        def demander_bloc(action="lire"):
            while True:
                bloc_str = input(f"Numero du bloc a {action} (0 a 5) : ").strip()

                if not bloc_str.isdigit():
                    print("Saisie incorrecte : veuillez entrer un numero entre 0 et 5.")
                    continue
                bloc = int(bloc_str)
                if bloc < 0 or bloc > 5:
                    print("Bloc invalide : valeur hors limites.")
                    print("Veuillez entrer un numero entre 0 et 5.")
                    continue

                if self.mifare.est_bloc_remorque(bloc):
                    print("Lecture bloc remorque impossible")
                    continue

                return bloc

        while True:
            print("\n--- Menu Bloc ---")
            print("1. Lire l'id")
            print("2. Lire les credits")

            print("3. Ecrire un bloc")
            print("4. Quitter le menu bloc")
            choix = input("Votre choix : ").strip()

            if choix == "1":
                uid_carte = self.attendre_carte("Approchez la carte a lire...")

                error, contenu = self.mifare.lire_bloc(uid_carte, 4)
                if not error and any(contenu):
                    print(f"Contenu : {block_list_to_string(contenu)}")
            elif choix == "2":
                uid_carte = self.attendre_carte("Approchez la carte a lire...")

                error, contenu = self.mifare.lire_bloc(uid_carte, 5)
                if not error and any(contenu):
                    print(f"Contenu : {block_list_to_integer(contenu)}")

            elif choix == "3":
                bloc = demander_bloc("ecrire")

                texte = input("Texte : ")
                uid_carte = self.attendre_carte("Approchez la carte pour ecrire...")

                block_list = string_to_block_list(texte)
                error = self.mifare.ecrire_bloc(uid_carte, bloc, block_list)
                if not error:
                    print(f"Ecriture effectue avec succes!")

            elif choix == "4":
                break
