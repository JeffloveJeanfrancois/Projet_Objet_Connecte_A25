# ---- Conversion helpers ----
def str_to_block(s: str) -> bytes:
    b = s.encode("ascii")[:16]
    return b.ljust(16, b"\x00")

def block_to_str(b: bytes) -> str:
    return b.split(b"\x00", 1)[0].decode("ascii", errors="ignore")

def int_to_block(n: int) -> bytes:
    return n.to_bytes(4, "big") + b"\x00" * 12

def block_to_int(b: bytes) -> int:
    return int.from_bytes(b[:4], "big")


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
    BLOCK_ID = 1
    BLOCK_COUNTER = 2
    MAX_COUNTER = 999

    def __init__(self, reader):
        self.reader = reader

    # ---- ID ----
    def read_card_id(self, uid):
        data = self.reader.read_block(uid, self.BLOCK_ID)
        if not data:
            raise ReadError(uid)
        return block_to_str(data)

    def write_card_id(self, uid, card_id: str):
        success = self.reader.write_block(uid, self.BLOCK_ID, str_to_block(card_id))
        if not success:
            raise WriteError(uid)
        return success

    # ---- COUNTER ----
    def read_counter(self, uid):
        data = self.reader.read_block(uid, self.BLOCK_COUNTER)
        if not data:
            raise ReadError(uid, "Impossible de lire le compteur")
        return block_to_int(data)

    def write_counter(self, uid, value: int):
        success = self.reader.write_block(uid, self.BLOCK_COUNTER, int_to_block(value))
        if not success:
            raise WriteError(uid, "Impossible de modifier le compteur")
        return success

    def decrement(self, uid, amount=1):
        if amount < 0:
            raise ValueError("Le montant ne peut pas etre negatif")
        
        count = self.read_counter(uid)
        
        if amount > count:
            raise InsufficientCounter(uid, amount, count)
        
        return self.write_counter(uid, count - amount)

    def increment(self, uid, amount=1):
        if amount < 0:
            raise ValueError("Le montant ne peut pas etre negatif")
        
        count = self.read_counter(uid)
        new_value = count + amount
        
        if new_value >= self.MAX_COUNTER:
            new_value = self.MAX_COUNTER
            print(f"Compteur max atteint pour UID {uid}")
            
        return self.write_counter(uid, new_value)
