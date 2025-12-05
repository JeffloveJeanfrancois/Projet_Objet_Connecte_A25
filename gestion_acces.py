import threading

class GestionAcces:
    def __init__(self, feedback, ecran=None):
        self.feedback = feedback
        self.ecran = ecran

    def carte_acceptee(self, nom=""):
        threads = []

        # 1. Préparer le thread LED (vert)
        t_led = threading.Thread(target=self.feedback.vert, args=(2,))
        threads.append(t_led)

        # 2. Préparer le thread Bip
        t_bip = threading.Thread(target=self.feedback.bip, args=(0.2,))
        threads.append(t_bip)

        # 3. Préparer le thread Écran (IMPORTANT : on le met dans un thread aussi)
        if self.ecran:
            # On utilise kwargs pour passer les arguments proprement
            t_ecran = threading.Thread(
                target=self.ecran.afficher, 
                kwargs={
                    "ligne1": "ACCES ACCEPTE", 
                    "ligne2": f"Bienvenue {nom}"[:16], 
                    "duree": 2  # Durée affichage succès
                }
            )
            threads.append(t_ecran)

        # 4. Démarrer TOUS les threads en même temps
        for t in threads:
            t.start()

        # 5. Attendre la fin du thread le plus long (ici l'écran ou la LED)
        # Cela empêche de lire une nouvelle carte pendant l'affichage
        for t in threads:
            t.join()

    def carte_refusee(self):
        threads = []

        # 1. LED Rouge (2 secondes)
        t_led = threading.Thread(target=self.feedback.rouge, args=(2,))
        threads.append(t_led)

        # 2. Bip (plus long pour refus)
        t_bip = threading.Thread(target=self.feedback.bip, args=(0.8,))
        threads.append(t_bip)

        # 3. Écran (4 secondes comme demandé)
        if self.ecran:
            t_ecran = threading.Thread(
                target=self.ecran.afficher,
                kwargs={
                    "ligne1": "ACCES REFUSE", 
                    "ligne2": "Carte Invalide", 
                    "duree": 4  # C'est ici que le 4 secondes est géré
                }
            )
            threads.append(t_ecran)

        # 4. Tout lancer simultanément
        for t in threads:
            t.start()

        # 5. Attendre que l'affichage de 4s soit fini avant de rendre la main
        for t in threads:
            t.join()