from rfid_lecteur import LecteurRFID
from card_utils import block_list_to_string, block_list_to_integer, string_to_block_list, integer_to_block_list
from card_exceptions import ReadError, WriteError, AuthError

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
    def read_card_id(self, uid: list[int]) -> str:
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

    def write_card_id(self, uid: list[int], card_id: str) -> None:
        """Write the card ID to the RFID card.
        Args:
            uid: UID of the card.
            card_id: The new card ID to write.
        Raises:
            WriteError: If writing the block fails.
        """
        block_data = string_to_block_list(card_id)
        error = self.reader.ecrire_bloc(uid, self.ID_BLOCK, block_data)
        if error:
            raise WriteError(uid)

    # ---- COUNTER ----
    def read_counter(self, uid: list[int]) -> int:
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

    def write_counter(self, uid: list[int], value: int) -> None:
        """Write a new counter value to the RFID card.
        Args:
            uid: UID of the card.
            value: The counter value to write.
        Raises:
            WriteError: If writing the block fails.
        """
        block_data = integer_to_block_list(value)
        error = self.reader.ecrire_bloc(uid, self.COUNTER_BLOCK, block_data)
        if error:
            raise WriteError(uid, "Impossible de modifier le compteur")

    def decrement(self, uid: list[int], amount=1) -> tuple[bool, int]:
        """Decrement the counter on the RFID card.
        Args:
            uid: UID of the card.
            amount: Amount to decrement (default is 1).
        Returns:
            tuple[bool, int]: (success, new_counter_value). Success is False if
            the decrement would result in a negative value.
        Raises:
            ValueError: If amount is negative.
            AuthError: If authentication to the counter block fails.
            ReadError: If reading the counter fails.
            WriteError: If writing the new counter fails.
        """
        if amount < 0:
            raise ValueError("Le montant ne peut pas etre negatif")
        
        if not self.reader.authentifier(uid, 5):
            raise AuthError(uid, self.COUNTER_BLOCK, "Auth echouee pour le bloc du compteur")

        try:
            error, data = self.reader.rdr.read(5)
            if error or data is None or len(data) != self.BLOCK_SIZE:
                raise ReadError(uid, "Impossible de lire le compteur correctement")
            
            current_count = block_list_to_integer(data)

            if amount > current_count:
                print(f"Impossible de reduire le compteur: demande {amount}, disponible {current_count} (UID: {uid})")
                return False, current_count
            
            new_count = current_count - amount
            block_data = integer_to_block_list(new_count)

            error = self.reader.rdr.write(5, block_data)
            if error:
                raise WriteError(uid, "Impossible de modifier le compteur")

            return True, new_count
        finally:
            # Always stop crypto
            self.reader.rdr.stop_crypto()

    def increment(self, uid: list[int], amount=1) -> int:
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
        
        if not self.reader.authentifier(uid, 5):
            raise AuthError(uid, self.COUNTER_BLOCK, "Auth echouee pour le bloc du compteur")
        
        try:
            error, data = self.reader.rdr.read(5)
            if error or data is None or len(data) != self.BLOCK_SIZE:
                raise ReadError(uid, "Impossible de lire le compteur correctement")
            
            current_count = block_list_to_integer(data)
            new_count = current_count + amount
            
            if new_count >= self.MAX_COUNTER:
                new_count = self.MAX_COUNTER
                print(f"Compteur max atteint pour UID {uid}")
                
            block_data = integer_to_block_list(new_count)
            
            error = self.reader.rdr.write(5, block_data)
            if error:
                raise WriteError(uid, "Impossible de modifier le compteur")
            
            return True, new_count
        finally:
            # Always stop crypto
            self.reader.rdr.stop_crypto()
