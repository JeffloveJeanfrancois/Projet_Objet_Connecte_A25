from rfid_lecteur import LecteurRFID
from card_utils import block_list_to_string, block_list_to_integer, string_to_block_list, integer_to_block_list
from card_exceptions import ReadError, WriteError, AuthError
from typing import Optional

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
    def read_card_id(self, uid: Optional[list[int]] = None, auto_auth: bool = True) -> str:
        """Read the card ID from the RFID card.
        Args:
            uid: UID of the card (required if auto_auth=True).
            auto_auth: 
                - True: authentifie automatiquement et stop_crypto() après.
                - False: laisse l'appelant gérer l'authentification.
        Returns:
            str: The card ID as a string.
        Raises:
            ValueError: If auto_auth=True but uid is None.
            ReadError: If reading the block fails.
        """
        if auto_auth and uid is None:
            raise ValueError("uid est requis lorsque auto_auth est vrai.")

        error, data = self.reader.lire_bloc(self.ID_BLOCK, uid, auto_auth)
        if error or data is None or len(data) != self.BLOCK_SIZE:
            raise ReadError(uid)
        return block_list_to_string(data)

    def write_card_id(self, card_id: str, uid: Optional[list[int]] = None, auto_auth: bool = True) -> None:
        """Write the card ID to the RFID card.
        Args:
            card_id: The new card ID to write.
            uid: UID of the card (required if auto_auth=True).
            auto_auth: 
                - True: authentifie automatiquement et stop_crypto() après.
                - False: laisse l'appelant gérer l'authentification.
        Raises:
            ValueError: If auto_auth=True but uid is None.
            WriteError: If writing the block fails.
        """
        if auto_auth and uid is None:
            raise ValueError("uid est requis lorsque auto_auth est vrai.")
        
        block_data = string_to_block_list(card_id)
        error = self.reader.ecrire_bloc(self.ID_BLOCK, block_data, uid, auto_auth)
        if error:
            raise WriteError(uid)

    # ---- COUNTER ----
    def read_counter(self, uid: Optional[list[int]] = None, auto_auth: bool = True) -> int:
        """Read the counter value from the RFID card.
        Args:
            uid: UID of the card (required if auto_auth=True).
            auto_auth: 
                - True: authentifie automatiquement et stop_crypto() après.
                - False: laisse l'appelant gérer l'authentification.
        Returns:
            int: The current counter value.
        Raises:
            ValueError: If auto_auth=True but uid is None.
            ReadError: If reading the block fails.
        """
        if auto_auth and uid is None:
            raise ValueError("uid est requis lorsque auto_auth est vrai.")

        error, data = self.reader.lire_bloc(self.COUNTER_BLOCK, uid, auto_auth)
        if error or data is None or len(data) != self.BLOCK_SIZE:
            raise ReadError(uid, "Impossible de lire le compteur correctement")
        return block_list_to_integer(data)

    def write_counter(self, value: int, uid: Optional[list[int]] = None, auto_auth: bool = True) -> None:
        """Write a new counter value to the RFID card.
        Args:
            value: The counter value to write.
            uid: UID of the card (required if auto_auth=True).
            auto_auth: 
                - True: authentifie automatiquement et stop_crypto() après.
                - False: laisse l'appelant gérer l'authentification.
        Raises:
            ValueError: If auto_auth=True but uid is None.
            WriteError: If writing the block fails.
        """
        if auto_auth and uid is None:
            raise ValueError("uid est requis lorsque auto_auth est vrai.")

        block_data = integer_to_block_list(value)
        error = self.reader.ecrire_bloc(self.COUNTER_BLOCK, block_data, uid, auto_auth)
        if error:
            raise WriteError(uid, "Impossible de modifier le compteur")

    def decrement(self, uid: list[int], amount=1) -> tuple[bool, int]:
        """Decrement the counter on the RFID card.
        Args:
            uid: UID of the card.
            amount: Amount to decrement (default is 1).
        Returns:
            tuple: [bool, int] (success, new_counter_value). 
                - Success is False if the decrement would result in a negative value.
        Raises:
            ValueError: If amount is negative.
            AuthError: If authentication to the counter block fails.
            ReadError: If reading the counter fails.
            WriteError: If writing the new counter fails.
        """
        if amount < 0:
            raise ValueError("Le montant ne peut pas etre negatif")
        
        if not self.reader.authentifier(uid, self.COUNTER_BLOCK):
            raise AuthError(uid, self.COUNTER_BLOCK, "Auth echouee pour le bloc du compteur")

        try:            
            current_count = self.read_counter(auto_auth=False)

            if amount > current_count:
                print(f"Impossible de reduire le compteur: demande {amount}, disponible {current_count} (UID: {uid})")
                return False, current_count
            
            new_count = current_count - amount

            self.write_counter(new_count, auto_auth=False)

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
            AuthError: If authentication to the counter block fails.
            ReadError: If reading the counter fails.
            WriteError: If writing the new counter fails.
        """
        if amount < 0:
            raise ValueError("Le montant ne peut pas etre negatif")
        
        if not self.reader.authentifier(uid, self.COUNTER_BLOCK):
            raise AuthError(uid, self.COUNTER_BLOCK, "Auth echouee pour le bloc du compteur")
        
        try:
            current_count = self.read_counter(auto_auth=False)
            
            new_count = current_count + amount
            
            if new_count >= self.MAX_COUNTER:
                new_count = self.MAX_COUNTER
                print(f"Compteur max atteint pour UID {uid}")
                
            self.write_counter(new_count, auto_auth=False)
            
            return new_count
        finally:
            # Always stop crypto
            self.reader.rdr.stop_crypto()
