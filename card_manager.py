from rfid_lecteur import LecteurRFID
from card_utils import block_list_to_string, block_list_to_integer
from card_exceptions import ReadError, WriteError

class CardService:
    """Service for reading and writing RFID card data."""

    ID_BLOCK = 4
    COUNTER_BLOCK = 5
    MAX_COUNTER = 999
    BLOCK_SIZE = 16

    def __init__(self, reader: LecteurRFID):
        """Initialize the card service.
        Args:
            reader: An instance of LecteurRFID used to read/write cards.
        """
        self.reader = reader

    # ---- ID ----
    def read_card_id(self, uid) -> str:
        """Read the card ID from the RFID card.
        Args:
            uid: UID of the card.
        Returns:
            str: The card ID as a string.
        Raises:
            ReadError: If reading the block fails.
        """
        error, data = self.reader.lire_bloc(uid, self.ID_BLOCK)
        if error or data is None or len(data) != self.BLOCK_SIZE:
            raise ReadError(uid)
        return block_list_to_string(data)

    def write_card_id(self, uid, card_id: str) -> None:
        """Write the card ID to the RFID card.
        Args:
            uid: UID of the card.
            card_id: The new card ID to write.
        Raises:
            WriteError: If writing the block fails.
        """
        error = self.reader.ecrire_bloc(uid, self.ID_BLOCK, card_id)
        if error:
            raise WriteError(uid)

    # ---- COUNTER ----
    def read_counter(self, uid) -> int:
        """Read the counter value from the RFID card.
        Args:
            uid: UID of the card.
        Returns:
            int: The current counter value.
        Raises:
            ReadError: If reading the block fails.
        """
        error, data = self.reader.lire_bloc(uid, self.COUNTER_BLOCK)
        if error or data is None or len(data) != self.BLOCK_SIZE:
            raise ReadError(uid, "Impossible de lire le compteur correctement")
        return block_list_to_integer(data)

    def write_counter(self, uid, value: int) -> None:
        """Write a new counter value to the RFID card.
        Args:
            uid: UID of the card.
            value: The counter value to write.
        Raises:
            WriteError: If writing the block fails.
        """
        error = self.reader.ecrire_bloc(uid, self.COUNTER_BLOCK, str(value))
        if error:
            raise WriteError(uid, "Impossible de modifier le compteur")

    def decrement(self, uid, amount=1) -> tuple[bool, int]:
        """Decrement the counter on the RFID card.
        Args:
            uid: UID of the card.
            amount: Amount to decrement (default is 1).
        Returns:
            tuple[bool, int]: (success, new_counter_value). Success is False if
            the decrement would result in a negative value.
        Raises:
            ValueError: If amount is negative.
            WriteError: If writing the new counter fails.
        """
        if amount < 0:
            raise ValueError("Le montant ne peut pas etre negatif")
        
        count = self.read_counter(uid)
        
        if amount > count:
            print(f"Impossible de reduire le compteur: demande {amount}, disponible {count} (UID: {uid})")
            return False, count
        else:
            new_count = count - amount
            self.write_counter(uid, new_count)
            return True, new_count

    def increment(self, uid, amount=1) -> int:
        """Increment the counter on the RFID card.
        Args:
            uid: UID of the card.
            amount: Amount to increment (default is 1).
        Returns:
            int: The new counter value (capped at MAX_COUNTER).
        Raises:
            ValueError: If amount is negative.
            WriteError: If writing the new counter fails.
        """
        if amount < 0:
            raise ValueError("Le montant ne peut pas etre negatif")
        
        count = self.read_counter(uid)
        new_value = count + amount
        
        if new_value >= self.MAX_COUNTER:
            new_value = self.MAX_COUNTER
            print(f"Compteur max atteint pour UID {uid}")
        
        self.write_counter(uid, new_value)
        
        return new_value
