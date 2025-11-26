class InterfaceAdmin:

    def __init__(self, gestion_cartes):
        self.cartes = gestion_cartes

    def lancer(self, uid_admin):
        print("\n=== MODE ADMIN ===")
        print("1 → Ajouter / Modifier une carte")
        print("2 → Quitter mode admin")

        choix = input("Choix : ")

        if choix == "1":
            self.ajouter_modifier()
        else:
            print("Sortie du mode admin.")

    def ajouter_modifier(self):
        uid = input("UID de la carte : ")
        nom = input("Nom : ")
        actif = input("Actif ? (o/n) : ").lower() == 'o'

        self.cartes.ajouter_ou_modifier(uid, nom, actif)
        print("Carte enregistrée.")
