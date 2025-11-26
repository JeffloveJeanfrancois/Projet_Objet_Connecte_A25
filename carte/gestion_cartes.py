import json
import os

class GestionCartes:

    def __init__(self, fichier="data/cartes_autorisees.json"):
        self.fichier = fichier
        self.cartes = self._charger()

    def _charger(self):
        if not os.path.exists(self.fichier):
            return {}
        with open(self.fichier, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return {c["uid"]: c for c in data.get("cartes", [])}

    def verifier(self, uid):
        if uid not in self.cartes:
            return False, "Inconnu", "Carte non autorisée"
        c = self.cartes[uid]
        if not c["actif"]:
            return False, c["nom"], "Carte désactivée"
        return True, c["nom"], "Accepté"
