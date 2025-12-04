from card_reader import CardReader
from configuration_carte import CarteConfiguration

# ---- Custom exceptions ----
class CardError(Exception):
    """Base exception for card operations"""
    pass

class ReadError(CardError):
    def __init__(self, uid, message="Impossible de lire la carte"):
        super().__init__(f"{message} (UID: {uid})")
        self.uid = uid

class WriteError(CardError):
    def __init__(self, uid, message="Impossible d'ecrire sur la carte"):
        super().__init__(f"{message} (UID: {uid})")
        self.uid = uid

class InsufficientCounter(CardError):
    def __init__(self, uid, requested, available):
        super().__init__(f"Impossible de reduire le compteur: demande {requested}, disponible {available} (UID: {uid})")
        self.uid = uid
        self.requested = requested
        self.available = available


class CardService:
    BLOCK_ID = 4
    BLOCK_COUNTER = 5
    MAX_COUNTER = 999

    def __init__(self, reader: CarteConfiguration):
        self.reader = reader

    # ---- ID ----
    def read_card_id(self, uid):
        data = self.reader.lire_bloc(uid, self.BLOCK_ID)
        if not data:
            raise ReadError(uid)
        return block_list_to_str(data)

    def write_card_id(self, uid, card_id: str):
        success = self.reader.ecrire_bloc(uid, self.BLOCK_ID, card_id)
        if not success:
            raise WriteError(uid)
        return success

    # ---- COUNTER ----
    def read_counter(self, uid):
        data = self.reader.lire_bloc(uid, self.BLOCK_COUNTER)
        if not data:
            raise ReadError(uid, "Impossible de lire le compteur")
        return block_list_to_int(data)

    def write_counter(self, uid, value: int):
        success = self.reader.ecrire_bloc(uid, self.BLOCK_COUNTER, str(value))
        if not success:
            raise WriteError(uid, "Impossible de modifier le compteur")
        return success

    def decrement(self, uid, amount=1):
        if amount < 0:
            raise ValueError("Le montant ne peut pas etre negatif")
        
        count = self.read_counter(uid)
        
        if amount > count:
            print(f"Impossible de reduire le compteur: demande {amount}, disponible {count} (UID: {uid})")
            return False, count
        else:
            success = self.write_counter(uid, count - amount)
            return success, amount

    def increment(self, uid, amount=1):
        if amount < 0:
            raise ValueError("Le montant ne peut pas etre negatif")
        
        count = self.read_counter(uid)
        new_value = count + amount
        
        if new_value >= self.MAX_COUNTER:
            new_value = self.MAX_COUNTER
            print(f"Compteur max atteint pour UID {uid}")
            
        return self.write_counter(uid, new_value)
