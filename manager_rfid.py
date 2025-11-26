import json
import os

class RFIDManager:
    def __init__(self, file_path="rfid_cards.json"):
        self.file_path = file_path
        self.cards = self.load_cards()

    def load_cards(self):
        if not os.path.exists(self.file_path):
            return {}
        with open(self.file_path, "r") as f:
            return json.load(f)

    def save_cards(self):
        with open(self.file_path, "w") as f:
            json.dump(self.cards, f, indent=4)

    def add_card(self, card_id, uses):
        self.cards[card_id] = uses
        self.save_cards()
        print(f"Carte {card_id} ajoutée avec {uses} utilisations.")

    def access_card(self, card_id):
        if card_id not in self.cards:
            print("Carte non valide.")
            return
        if self.cards[card_id] <= 0:
            print("Compte vide")
            return
        self.cards[card_id] -= 1
        self.save_cards()
        print(f"Accès autorisé. Utilisations restantes : {self.cards[card_id]}")

    def reset_card(self, card_id, new_uses):
        if card_id not in self.cards:
            print("Carte non valide.")
            return
        self.cards[card_id] = new_uses
        self.save_cards()
        print(f"Compteur de la carte {card_id} réinitialisé à {new_uses} utilisations.")


# --- Exemple d'utilisation ---
if __name__ == "__main__":
    manager = RFIDManager()
    manager.add_card("123ABC", 5)
    manager.access_card("123ABC")
    manager.reset_card("123ABC", 5)
