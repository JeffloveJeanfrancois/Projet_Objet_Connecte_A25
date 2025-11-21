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

    def filtrer_historique(self, filtre_choisi: str) -> dict:
       
        filtre = filtre_choisi.lower()
        entrees_filtrees = []
        
        # Filtrage des entrées
        for entree in self.entrees_historique:
            type_acces = self._determiner_type_acces(entree['statut'])
            
            if filtre == 'tous' or filtre == type_acces:
                entree_complete = entree.copy()
                entree_complete['type_acces'] = type_acces
                entrees_filtrees.append(entree_complete)
        
        statistiques = {
            'autorisé': 0,
            'refusé': 0,
            'alerte': 0,
            'désactivé': 0,
            'indéterminé': 0
        }
        
        for entree in self.entrees_historique:
            type_acces = self._determiner_type_acces(entree['statut'])
            statistiques[type_acces] = statistiques.get(type_acces, 0) + 1
        
        return {
            'entrees': entrees_filtrees,
            'nombre_total': len(self.entrees_historique),
            'nombre_filtre': len(entrees_filtrees),
            'filtre_applique': filtre,
            'statistiques': statistiques
        }
    
    def afficher_filtre(self, filtre: str):
        """Affiche l'historique filtré de manière simplifiée"""
        resultat = self.filtrer_historique(filtre)
        
        print(f"\n=== FILTRE: {resultat['filtre_applique'].upper()} ===")
        print(f"Résultats: {resultat['nombre_filtre']} / {resultat['nombre_total']} entrées\n")
        
        if resultat['entrees']:
            print(f"{'Date/Heure':<20} | {'Type':<10} | {'UID':<20} | {'Nom':<20} | {'Statut':<15}")
            print("-" * 95)
            for entree in resultat['entrees']:
                print(f"{entree['date_heure']:<20} | {entree['type_carte']:<10} | {entree['uid']:<20} | "
                      f"{entree['nom']:<20} | {entree['type_acces'].upper():<15}")
        else:
            print(f"Aucune entrée pour le filtre '{filtre}'")


def afficher_menu():
    """Affiche le menu de sélection des filtres"""
    print("\n" + "=" * 60)
    print("MENU DE FILTRAGE")
    print("=" * 60)
    print("1. Afficher tous les accès")
    print("2. Afficher uniquement les accès AUTORISÉS")
    print("3. Afficher uniquement les accès REFUSÉS")
    print("4. Afficher uniquement les ALERTES")
    print("5. Afficher uniquement les cartes DÉSACTIVÉES")
    print("6. Afficher les statistiques globales")
    print("0. Quitter")
    print("=" * 60)


def main():
    historique = HistoriqueDesAcces()
    
    while True:
        afficher_menu()
        
        try:
            choix = input("\nVotre choix: ").strip()
            
            if choix == '0':
                print("\nArrêt de l'historique")
                break
            elif choix == '1':
                historique.afficher_historique()
            elif choix == '2':
                historique.afficher_filtre('autorisé')
            elif choix == '3':
                historique.afficher_filtre('refusé')
            elif choix == '4':
                historique.afficher_filtre('alerte')
            elif choix == '5':
                historique.afficher_filtre('désactivé')
            elif choix == '6':
                resultat = historique.filtrer_historique('tous')
                print("\n=== STATISTIQUES GLOBALES ===")
                print(f"Total: {resultat['nombre_total']} entrées\n")
                
                for type_acces, count in resultat['statistiques'].items():
                    pourcentage = (count / resultat['nombre_total'] * 100) if resultat['nombre_total'] > 0 else 0
                    print(f"{type_acces.capitalize()}: {count} ({pourcentage:.1f}%)")
            else:
                print("\nChoix invalide. Veuillez sélectionner une option du menu.")
            
            input("\nAppuyez sur Entrée pour continuer...")
            
        except KeyboardInterrupt:
            print("\n\nInterruption détectée. Au revoir!")
            break
        except Exception as exception:
            print(f"\nErreur: {exception}")
            input("\nAppuyez sur Entrée pour continuer...")

if __name__ == "__main__":
    main()