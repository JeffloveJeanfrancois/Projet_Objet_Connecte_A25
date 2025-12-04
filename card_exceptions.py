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
