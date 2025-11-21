import csv
import json
import os
import sys
from typing import List, Dict, Optional


class HistoriqueDesAcces:
    def __init__(self):
        self.fichier_historique = "journal_rfid.csv"
        self.fichier_cartes = "cartes_autorisees.json"
        self.cartes_autorisees = self._charger_cartes_autorisees()
        self.entrees_historique = self._charger_historique()
    
    def _charger_cartes_autorisees(self) -> Dict:
        if not os.path.exists(self.fichier_cartes):
            print(f"Le fichier {self.fichier_cartes} n'existe pas")
            sys.exit(1)
        
        try:
            with open(self.fichier_cartes, 'r') as fichier:
                data = json.load(fichier)
                resultat = {}
                for carte in data.get('cartes', []):
                    uid = carte.get('uid')
                    if uid:
                        resultat[carte['uid']] = {
                            'nom': carte.get('nom', 'Inconnu'),
                            'actif': carte.get('actif', False)
                        }
                return resultat
        except Exception as exception:
            print(f"Erreur lors du chargement des cartes: {exception}")
            return {}
    
    def _charger_historique(self) -> List[Dict]:
        if not os.path.exists(self.fichier_historique):
            print(f"Le fichier {self.fichier_historique} n'existe pas.")
            sys.exit(1)
        
        try:
            with open(self.fichier_historique, 'r') as fichier:
                reader = csv.DictReader(fichier)
                entrees_historique = []
                for ligne in reader:
                    entree = self._parser_ligne(ligne)
                    if entree:
                        entrees_historique.append(entree)
                return entrees_historique
        except Exception as exception:
            print(f"Erreur lors de la lecture du fichier: {exception}")
            sys.exit(1)
            
    
    def afficher_historique(self):
        if not self.entrees_historique:
            print("Erreur: Aucune entrée dans l'historique.")
            sys.exit(1)
        
        entrees_filtrees = self.entrees_historique
        
        # En-tête
        print("\n" + "=" * 100)
        print(f"HISTORIQUE DES ACCÈS")
        print("=" * 100)
        print("-" * 100)
        
        # Affichage des entrées
        for entree in entrees_filtrees:
            type_acces = self._determiner_type_acces(entree['statut'])
            resultat = type_acces.upper() if type_acces != 'indéterminé' else entree['statut']
            
            print(f"{entree['date_heure']:<20} | {entree['uid']:<25} | {entree['nom']:<20} | "
                  f"{entree['type_carte']:<8} | {resultat:<15}")
        
        print("=" * 100)
        print(f"\nTotal: {len(entrees_filtrees)} entrée(s)")


def main():
    historique = HistoriqueDesAcces()
    
    historique.afficher_historique()


if __name__ == "__main__":
    main()