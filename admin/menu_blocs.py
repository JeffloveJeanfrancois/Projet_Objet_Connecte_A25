from carte.configuration_carte import CarteConfiguration

class MenuBlocs:

    def __init__(self):
        self.cfg = CarteConfiguration()

    def ouvrir(self, uid):
        while True:
            print("\n--- Menu Blocs ---")
            print("1. Lire un bloc")
            print("2. Écrire un bloc")
            print("3. Retour")
            choix = input("> ")

            if choix == "1":
                bloc = int(input("Bloc : "))
                print(self.cfg.lire_bloc(uid, bloc))

            elif choix == "2":
                bloc = int(input("Bloc : "))
                texte = input("Texte : ")
                self.cfg.ecrire_bloc(uid, bloc, texte)

            elif choix == "3":
                return
