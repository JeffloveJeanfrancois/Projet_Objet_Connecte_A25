BLOCK_SIZE = 16
INT_SIZE = 4
PADDING_BYTE = b"\x00"

# ---- Conversion helpers (bytes) ----
def string_to_block_bytes(text: str) -> bytes:
    """
    Convert a string to a 16-byte MIFARE block.
    Only ASCII characters are supported. Truncates to 16 bytes and pads with zeros.
    Non-ASCII characters are replaced with '?'.
    """
    encoded_bytes = text.encode("ascii", errors="replace")[:BLOCK_SIZE]
    padded_bytes = encoded_bytes.ljust(BLOCK_SIZE, PADDING_BYTE)
    return padded_bytes

def block_bytes_to_string(block_bytes: bytes) -> str:
    """
    Convert a 16-byte MIFARE block to a string.
    Stops at the first zero byte. Non-ASCII characters are replaced with '?'.
    """
    data_up_to_zero = block_bytes.split(PADDING_BYTE, 1)[0]
    return data_up_to_zero.decode("ascii", errors="replace")

def integer_to_block_bytes(value: int) -> bytes:
    """
    Convert an integer to a 16-byte MIFARE block.
    Stores the integer in the first 4 bytes (big endian) and pads the rest with zeros.
    """
    int_bytes = value.to_bytes(INT_SIZE, "big")
    padded_bytes = int_bytes + PADDING_BYTE * (BLOCK_SIZE - len(int_bytes))
    return padded_bytes

def block_bytes_to_integer(block_bytes: bytes) -> int:
    """
    Convert a 16-byte MIFARE block to an integer.
    Reads the first 4 bytes as a big endian integer.
    """
    int_bytes = block_bytes[:INT_SIZE]
    return int.from_bytes(int_bytes, "big")

# ---- Conversion helpers for pirc522 (list[int]) ----
def string_to_block_list(text: str) -> list[int]:
    """
    Convert a string to a 16-byte MIFARE block represented as list[int] for pirc522.
    Only ASCII characters are supported. Truncates to 16 bytes and pads with zeros.
    Non-ASCII characters are replaced with '?'.
    """
    return list(string_to_block_bytes(text))

def block_list_to_string(block_data: list[int]) -> str:
    """
    Convert a 16-byte block (list[int]) from pirc522 to a string.
    Stops at the first zero byte. Non-ASCII characters are replaced with '?'.
    """
    return block_bytes_to_string(bytes(block_data))

def integer_to_block_list(value: int) -> list[int]:
    """
    Convert an integer to a 16-byte block represented as list[int] for pirc522.
    Stores the integer in the first 4 bytes (big endian) and pads the rest with zeros.
    """
    return list(integer_to_block_bytes(value))

def block_list_to_integer(block_data: list[int]) -> int:
    """
    Convert a 16-byte block (list[int]) from pirc522 to an integer.
    Reads the first 4 bytes as big endian integer.
    """
    return block_bytes_to_integer(bytes(block_data[:INT_SIZE]))
