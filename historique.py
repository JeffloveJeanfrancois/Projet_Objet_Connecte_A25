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
                        resultat[uid] = {
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
    
    def _parser_ligne(self, ligne: Dict) -> Optional[Dict]:
        date_heure = ligne.get('Date/Heure')
        uid = ligne.get('UID')
        type_carte = ligne.get('Type de carte')
        nom = ligne.get('Nom')
        statut = ligne.get('Statut')
        
        if not date_heure or not uid:
            return None
        
        if not nom and uid in self.cartes_autorisees:
            nom = self.cartes_autorisees[uid]['nom']
        elif not nom:
            nom = "Inconnu"
        
        if not statut:
            if uid in self.cartes_autorisees:
                if self.cartes_autorisees[uid]['actif']:
                    statut = "Accepté"  
                else:
                    statut ="Carte désactivée"
            else:
                statut = "Refusé - Carte non autorisée"
        
        return {
            'date_heure': date_heure,
            'uid': uid,
            'type_carte': type_carte or 'Inconnu',
            'nom': nom,
            'statut': statut
        }
    
    def _determiner_type_acces(self, statut: str) -> str:
        statut_lower = statut.lower()
        
        if any(mot in statut_lower for mot in ['accepté', 'autorisé', 'autorise', 'valide', 'succès']):
            return 'autorisé'
        elif any(mot in statut_lower for mot in ['désactivé', 'desactive', 'carte désactivée']):
            return 'désactivé'
        elif any(mot in statut_lower for mot in ['alerte', 'suspicieux', 'tentative', 'illégitime']):
            return 'alerte'
        elif any(mot in statut_lower for mot in ['refusé', 'refuse', 'refus', 'non autorisé', 'invalide']):
            return 'refusé'
        else:
            return 'indéterminé'
    
    def afficher_historique(self):
        if not self.entrees_historique:
            print("Erreur: Aucune entrée dans l'historique.")
            sys.exit(1)
        
        # En-tête
        print("\n" + "=" * 100)
        print("HISTORIQUE DES ACCÈS")
        print("=" * 100)
        print(f"{'Date/Heure':<20} | {'UID':<25} | {'Nom':<20} | {'Type':<8} | {'Résultat':<15}")
        print("-" * 100)
        
        # Affichage des entrées
        for entree in self.entrees_historique:
            type_acces = self._determiner_type_acces(entree['statut'])
            resultat = type_acces.upper() if type_acces != 'indéterminé' else entree['statut']
            
            print(f"{entree['date_heure']:<20} | {entree['uid']:<25} | {entree['nom']:<20} | "
                  f"{entree['type_carte']:<8} | {resultat:<15}")
        
        print("=" * 100)
        print(f"\nTotal: {len(self.entrees_historique)} entrée(s)")

def main():
    historique = HistoriqueDesAcces()
    historique.afficher_historique()

if __name__ == "__main__":
    main()