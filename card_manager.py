from rfid_lecteur import LecteurRFID
from card_utils import block_list_to_string, block_list_to_integer

# ---- Custom exceptions ----
class CardError(Exception):
    """Base exception for card operations"""
    pass

class ReadError(CardError):
    def __init__(self, uid, message="Impossible de lire la carte correctement"):
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
    ID_BLOCK = 4
    COUNTER_BLOCK = 5
    MAX_COUNTER = 999
    BLOCK_SIZE = 16

    def __init__(self, reader: LecteurRFID):
        self.reader = reader

    # ---- ID ----
    def read_card_id(self, uid) -> str:
        error, data = self.reader.lire_bloc(uid, self.ID_BLOCK)
        if error or data is None or len(data) != self.BLOCK_SIZE:
            raise ReadError(uid)
        return block_list_to_string(data)

    def write_card_id(self, uid, card_id: str) -> bool:
        error = self.reader.ecrire_bloc(uid, self.ID_BLOCK, card_id)
        if error:
            raise WriteError(uid)
        return error

    # ---- COUNTER ----
    def read_counter(self, uid) -> int:
        error, data = self.reader.lire_bloc(uid, self.COUNTER_BLOCK)
        if error or data is None or len(data) != self.BLOCK_SIZE:
            raise ReadError(uid, "Impossible de lire le compteur correctement")
        return block_list_to_integer(data)

    def write_counter(self, uid, value: int) -> bool:
        error = self.reader.ecrire_bloc(uid, self.COUNTER_BLOCK, str(value))
        if error:
            raise WriteError(uid, "Impossible de modifier le compteur")
        return error

    def decrement(self, uid, amount=1):
        if amount < 0:
            raise ValueError("Le montant ne peut pas etre negatif")
        
        count = self.read_counter(uid)
        
        if amount > count:
            print(f"Impossible de reduire le compteur: demande {amount}, disponible {count} (UID: {uid})")
            return False, count
        else:
            new_count = count - amount
            error = self.write_counter(uid, new_count)
            return new_count

    def increment(self, uid, amount=1):
        if amount < 0:
            raise ValueError("Le montant ne peut pas etre negatif")
        
        count = self.read_counter(uid)
        new_value = count + amount
        
        if new_value >= self.MAX_COUNTER:
            new_value = self.MAX_COUNTER
            print(f"Compteur max atteint pour UID {uid}")
        
        error = self.write_counter(uid, new_value)
        
        return new_value
