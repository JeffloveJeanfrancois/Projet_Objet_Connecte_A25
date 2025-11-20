import time

def allumer_indicateur_visuel(couleur: str, duree_secondes: float):
    """Simule l'allumage d'une LED (verte ou rouge) pendant la durée spécifiée."""
    if couleur == "vert":
        symbole = "🟢"
        print(f"{symbole} Indicateur {couleur.upper()} allumé (Durée: {duree_secondes}s)")
    elif couleur == "rouge":
        symbole = "🔴"
        print(f"{symbole} Indicateur {couleur.upper()} allumé (Durée: {duree_secondes}s)")

def emettre_signal_sonore(type_bip: str, duree_secondes: float):
    """Simule l'émission d'un signal sonore (court ou long) avec la durée spécifiée."""
    if type_bip == "court":
        print(f"🔊 Signal sonore COURT émis (Durée: {duree_secondes}s)")
    elif type_bip == "long":
        print(f"🔊 Biiiiiiip long émis (Durée: {duree_secondes}s)")

def fournir_confirmation_acces(acces_autorise: bool):
    """
    Déclenche le feedback visuel et sonore selon le statut d'accès.
    
    :param acces_autorise: True si l'accès est accordé, False sinon.
    """
    print("\n" + "=" * 40)
    
    if acces_autorise:
        allumer_indicateur_visuel("vert", 2.0)
        emettre_signal_sonore("court", 0.2)
        print(">> CONSOLE : **Bienvenue**")
    else:
        allumer_indicateur_visuel("rouge", 2.0)
        emettre_signal_sonore("long", 0.8)
        print(">> CONSOLE : **Accès refusé**")
    
    print("=" * 40 + "\n")

if __name__ == "__main__":
    print("--- Démarrage du Module de Confirmation Utilisateur ---")

    # Test 1 : L'accès est accepté (votre coéquipier renvoie True)
    print("\n[SCÉNARIO 1 : TEST ACCÈS AUTORISÉ]")
    fournir_confirmation_acces(True)
    
    # Test 2 : L'accès est refusé (votre coéquipier renvoie False)
    print("\n[SCÉNARIO 2 : TEST ACCÈS REFUSÉ]")
    fournir_confirmation_acces(False)
    
    print("--- Validation logique de la Story 2 terminée ---")