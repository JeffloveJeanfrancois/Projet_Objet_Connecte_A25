from pirc522 import RFID

class RfidDriver:

    def __init__(self):
        self.r = RFID(pin_irq=None)

    def detecter_uid(self):
        (err, tag_type) = self.r.request()
        if err:
            return None

        (err, uid) = self.r.anticoll()
        if err:
            return None

        return "-".join(str(x) for x in uid)
