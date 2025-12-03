import threading


class GestionAcces:
    def __init__(self, feedback, ecran=None):
        self.feedback = feedback
        self.ecran = ecran

    def carte_acceptee(self, nom=""):
        # Lancer LED + bip simultanement
        thread_led = threading.Thread(target=self.feedback.vert, args=(2,))
        thread_bip = threading.Thread(target=self.feedback.bip, args=(0.2,))

        thread_led.start()
        thread_bip.start()

        thread_led.join()
        thread_bip.join()

        if self.ecran:
            self.ecran.afficher(
                ligne1="ACCES ACCEPTE",
                ligne2=f"Bienvenue {nom}"[:16],
                duree=4
            )

    def carte_refusee(self):
        thread_led = threading.Thread(target=self.feedback.rouge, args=(2,))
        thread_bip = threading.Thread(target=self.feedback.bip, args=(0.8,))

        thread_led.start()
        thread_bip.start()

        thread_led.join()
        thread_bip.join()

        if self.ecran:
            self.ecran.afficher(
                ligne1="ACCES REFUSE",
                ligne2="Carte Invalide",
                duree=4
            )
