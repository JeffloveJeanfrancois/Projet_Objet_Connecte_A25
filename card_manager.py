from card_reader import CardReader
from configuration_carte import CarteConfiguration

# ---- Conversion helpers (bytes) ----
def str_to_block(s: str) -> bytes:
    """
    Convert a string to a 16-byte MIFARE block.
    Only ASCII characters are supported. Truncates to 16 bytes and pads with zeros.
    """
    b = s.encode("ascii")[:16]
    return b.ljust(16, b"\x00")

def block_to_str(b: bytes) -> str:
    """
    Convert a 16-byte MIFARE block to a string.
    Stops at the first zero byte and ignores non-ASCII characters.
    """
    return b.split(b"\x00", 1)[0].decode("ascii", errors="ignore")

def int_to_block(n: int) -> bytes:
    """
    Convert an integer to a 16-byte MIFARE block.
    Stores the integer in the first 4 bytes (big endian) and pads the rest with zeros.
    """
    return n.to_bytes(4, "big") + b"\x00" * 12

def block_to_int(b: bytes) -> int:
    """
    Convert a 16-byte MIFARE block to an integer.
    Reads the first 4 bytes as a big endian integer.
    """
    return int.from_bytes(b[:4], "big")

# ---- Conversion helpers for pirc522 (list[int]) ----
def str_to_block_list(s: str) -> list[int]:
    """
    Convert a string to a 16-byte block represented as a list[int] for pirc522.
    Only ASCII characters are supported. Truncates to 16 bytes and pads with zeros.
    """
    b = s.encode("ascii")[:16]
    return list(b.ljust(16, b"\x00"))

def block_list_to_str(data: list[int]) -> str:
    """
    Convert a 16-byte block read from pirc522 (list[int]) back to a string.
    Stops at the first zero byte and ignores non-ASCII characters.
    """
    b = bytes(data)
    return b.split(b"\x00", 1)[0].decode("ascii", errors="ignore")

def int_to_block_list(n: int) -> list[int]:
    """
    Convert an integer to a 16-byte block represented as a list[int] for pirc522.
    Stores the integer in the first 4 bytes (little endian), pads the rest with zeros.
    """
    b = n.to_bytes(4, "little")
    b16 = b + b"\x00" * (16 - len(b))
    return list(b16)

def block_list_to_int(data: list[int]) -> int:
    """
    Convert a 16-byte block read from pirc522 (list[int]) back to an integer.
    Reads the first 4 bytes as little endian integer.
    """
    b = bytes(data[:4])
    return int.from_bytes(b, "little")


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