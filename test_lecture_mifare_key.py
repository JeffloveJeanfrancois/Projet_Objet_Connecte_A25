#!/usr/bin/env python3
import time
import RPi.GPIO as GPIO
from pirc522 import RFID

GPIO.setwarnings(False)

# Liste de clés communes
COMMON_KEYS = [
    [0xFF]*6,
    [0xA0]*6,
    [0x00]*6,
    [0xD3, 0xF7, 0xD3, 0xF7, 0xD3, 0xF7],
    [0xA1]*6,
    [0xB0]*6,
]

def est_bloc_trailer(bloc):
    """Retourne True si c'est le bloc remorque (dernier bloc du secteur)"""
    return (bloc + 1) % 4 == 0

def dump_carte():
    rdr = RFID(pin_irq=None)
    print("=== DUMP AUTOMATIQUE MIFARE CLASSIC (RC522) ===")
    print("Approchez une carte...\n")

    try:
        while True:
            error, _ = rdr.request()
            if error:
                time.sleep(0.1)
                continue

            print("Carte détectée !")

            error, uid = rdr.anticoll()
            if error:
                print("Erreur anticollision.")
                continue

            uid_str = "-".join(str(x) for x in uid)
            print(f"UID : {uid_str}\n")

            rdr.select_tag(uid)
            print("=== Lecture des blocs avec clés connues ===\n")

            for bloc in range(64):  # Mifare 1K
                #if est_bloc_trailer(bloc):
                    #print(f"[Bloc {bloc:02d}] TRAILER — clé & permissions (non affiché)")
                    #continue

                # On teste toutes les clés
                bloc_lu = False
                for key in COMMON_KEYS:
                    result = rdr.card_auth(rdr.auth_a, bloc, key, uid)
                    if result == 0:
                        status, data = rdr.read(bloc)
                        rdr.stop_crypto()
                        if status == 0 and data is not None:
                            texte = ''.join(chr(x) if 32 <= x <= 126 else '.' for x in data)
                            hexdata = " ".join(f"{x:02X}" for x in data)
                            print(f"[Bloc {bloc:02d}] Clé trouvée {key} | {hexdata} | {texte}")
                        else:
                            print(f"[Bloc {bloc:02d}] Clé trouvée {key} mais erreur lecture")
                        bloc_lu = True
                        break  # clé trouvée, passer au bloc suivant

                if not bloc_lu:
                    print(f"[Bloc {bloc:02d}] Aucun clé connue ne permet la lecture")

            print("\n=== FIN DUMP ===")
            print("Retirez la carte.\n")
            time.sleep(2)
            print("Approchez une nouvelle carte...\n")

    finally:
        rdr.cleanup()
        GPIO.cleanup()
        print("Nettoyage terminé.")

if __name__ == "__main__":
    dump_carte()
