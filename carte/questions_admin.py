import json
import os

class QuestionsAdmin:

    def __init__(self, fichier="data/pass.json"):
        self.fichier = fichier
        self.questions = self._charger()

    def _charger(self):
        if not os.path.exists(self.fichier):
            return {}
        with open(self.fichier, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return {e["uid"]: e for e in data.get("pass", [])}

    def verifier(self, uid, reponse):
        if uid not in self.questions:
            return True
        return reponse.lower() == self.questions[uid]["reponse"].lower()

    def get_question(self, uid):
        return self.questions.get(uid, {}).get("question", None)
