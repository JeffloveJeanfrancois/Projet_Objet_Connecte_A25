import time


class AdminInterface:
    def __init__(self, gestion_csv, mifare, questions_admin, attendre_carte):
        self.gestion_csv = gestion_csv
        self.mifare = mifare
        self.questions_admin = questions_admin
        self.attendre_carte = attendre_carte

    def autoriser_admin(self, uid_string):
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

    def run(self, uid_admin):
        print("\n=== Mode Admin active ===")

        while True:
            print("\nOptions :")
            print("1. Configurer une carte (Ajout/Modif + ecriture Blocs)")
            print("2. Quitter")
            choix = input("Votre choix: ")

            if choix == "1":
                uid_carte = self.attendre_carte("Veuillez approcher la carte a configurer...")
                uid_str = "-".join(str(octet) for octet in uid_carte)

                if uid_str in self.questions_admin:
                    print("\033[91mVous n'etes pas autorise a configurer cette carte (carte admin).\033[0m")
                    continue

                existe, nom_actuel, _, _, _ = self.gestion_csv.verifier_carte(uid_str)
                carte_trouvee = nom_actuel != "Non renseigne"

                nouveau_nom = nom_actuel if carte_trouvee else ""
                statut_actif = True
                nouveaux_credits = "0"

                if carte_trouvee:
                    print(f"Carte existante : Nom = {nom_actuel}")
                    conf = input("Ecraser ? (oui/non) : ").strip().lower()
                    if conf == "oui":
                        nouveau_nom = input("Nom : ").strip()
                        statut_actif = input("Activer ? (oui/non) : ").strip().lower() == "oui"
                        nouveaux_credits = input("Credits : ").strip()
                    else:
                        print("Menu de lecture/ecriture")
                        self.menu_configuration_blocs()
                        continue
                else:
                    print("Nouvelle carte.")
                    nouveau_nom = input("Nom : ").strip()
                    statut_actif = input("Activer ? (oui/non) : ").strip().lower() == "oui"
                    nouveaux_credits = input("Credits : ").strip()

                if not nouveaux_credits:
                    nouveaux_credits = "0"

                succes, id_genere = self.gestion_csv.ajouter_ou_modifier_carte(
                    uid_str, nouveau_nom, statut_actif, nouveaux_credits
                )

                if succes and id_genere:
                    print("\n[ECRITURE] Enregistrement sur la puce RFID...")
                    print(f" -> Bloc 4 (ID) : {id_genere}")
                    print(f" -> Bloc 5 (Credits) : {nouveaux_credits}")

                    uid_pour_ecriture = self.attendre_carte(
                        message=">>> Veuillez RESCANNER la carte maintenant pour finaliser l'ecriture... <<<"
                    )

                    ok_id = self.mifare.ecrire_bloc(uid_pour_ecriture, 4, str(id_genere))

                    time.sleep(0.2)

                    uid_pour_ecriture = self.attendre_carte(message=None)
                    ok_cred = self.mifare.ecrire_bloc(uid_pour_ecriture, 5, str(nouveaux_credits))

                    if ok_id and ok_cred:
                        print("[SUCCES] Carte entierement configuree (CSV + Puce) !")
                    else:
                        print("[ATTENTION] Une des ecritures a echoue. Verifiez les blocs.")

                self.menu_configuration_blocs()

            elif choix == "2":
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
            print("1. Lire un bloc")
            print("2. Ecrire un bloc")
            print("3. Quitter le menu bloc")
            choix = input("Votre choix : ").strip()

            if choix == "1":
                bloc = demander_bloc("lire")
                uid_carte = self.attendre_carte("Approchez la carte a lire...")

                contenu = self.mifare.lire_bloc(uid_carte, bloc)
                if contenu:
                    print(f"Contenu : {contenu}")

            elif choix == "2":
                bloc = demander_bloc("ecrire")

                texte = input("Texte : ")
                uid_carte = self.attendre_carte("Approchez la carte pour ecrire...")

                self.mifare.ecrire_bloc(uid_carte, bloc, texte)

            elif choix == "3":
                break
