import csv
import os
from typing import Iterable


class JournalRFID:
    def __init__(self, nom_fichier: str):
        self.nom_fichier = nom_fichier
        self._assurer_fichier()

    def _assurer_fichier(self):
        if os.path.exists(self.nom_fichier):
            return
        with open(self.nom_fichier, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Date/Heure", "UID", "Nom", "Statut"])

    def enregistrer(self, date: str, uid: Iterable[int], nom: str, statut: str):
        uid_str = "-".join(str(octet) for octet in uid)
        with open(self.nom_fichier, "a", newline="", encoding="utf-8") as fichier_csv:
            writer = csv.writer(fichier_csv)
            writer.writerow([date, uid_str, nom, statut])
