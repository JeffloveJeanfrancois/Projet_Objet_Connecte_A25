# Support de présentation — Projet Objets Connectés (Aligné sur les slides)

## 1. Objectif du projet

* Créer un **système de contrôle d’accès RFID** complet et fonctionnel.
* Inclure : authentification des cartes, gestion des utilisateurs et crédits, journalisation des accès.
* Fournir une **interface d’administration sécurisée** pour configurer les cartes.
* Assurer une **connexion MQTT sécurisée (TLS)** vers Azure pour la transmission des événements.

---

## 2. Démonstration — Comportement du système

### Carte acceptée

* Message *Bienvenue (nom)* affiché sur l’écran LCD.
* LED verte allumée + bip sonore.
* Log d’acceptation publié vers Azure MQTT.

### Carte refusée

* LED rouge activée.
* Log indiquant le refus.

---

## 3. Fonctionnement interne

* La boucle principale du `RFIDController.lancer()` gère :

  * Lecture RFID.
  * Anti-double scan.
  * Vérification CSV (autorisations).
  * Journalisation locale.
  * Publication MQTT.
  * Accès au mode administrateur.

* Le module `AdminInterface.configurer_carte` permet :

  * Menu interactif.
  * Configuration (nom, crédits).
  * Écriture des blocs via `CardService`.
  * Sécurisation par mot de passe admin.

* `mqtt_publisher.py` assure :

  * Connexion TLS 8883.
  * Chargement des certificats PEM.
  * Publication JSON vers Azure Event Grid MQTT.

* `CardService` gère les crédits :

  * Incrément/décrément.
  * Protection contre les valeurs négatives.

---

## 4. Matériel utilisé

* Raspberry Pi
* Lecteur RFID RC522
* Écran LCD I2C QAPASS
* LEDs (verte/rouge) + buzzer
* Cartes MIFARE

---

## 5. Avis sur le matériel

* **RC522** : fiable mais faible portée.
* **Raspberry Pi** : performance limitée sous charge.
* **LCD QAPASS** : lisible mais encombrant.
* **LEDs/buzzer** : très efficaces pour un retour immédiat.
* **Cartes MIFARE** : robustes mais sécurité limitée.

---

## 6. Logiciels et librairies

### Librairies principales

* Python 3
* pirc522
* RPi.GPIO
* RPLCD
* paho-mqtt (Azure MQTT TLS)
* Modules internes : `RFIDController`, `AdminInterface`, `CardService`, etc.

### Dépendances Python natives

* `time` : temporisation
* `os`, `pathlib` : gestion des fichiers
* `json` : sérialisation des logs MQTT
* `ssl` : certificat TLS
* `threading` : coordination LEDs/buzzer
* `csv` : fichiers d’autorisations
* `typing` : annotations pour clarifier le code

---

## 7. Difficultés rencontrées

### Problèmes MQTT/TLS Azure

* Génération correcte des clés et certificats.
* Paramétrage complet d’Azure : endpoint MQTT, port 8883, RBAC.
* Messages d’erreur peu explicites.

### Problèmes liés aux cartes

* Authentification bloc par bloc.
* Risque d’échec d’écriture.

### Interface administrateur

* Validation d’entrées nécessaire.
* Gestion de menus et sécurisation.

---

## 8. Solutions appliquées

* Analyse des erreurs TLS.
* Lecture approfondie de la documentation Azure.
* Ajustement des certificats et endpoints.
* Travail en équipe pour l’admin et la gestion CSV.
* Tests répétés de publication/souscription.

---

## 9. Conclusion 

* **Attentes** : Projet fonctionnel, formateur et techniquement stimulant.
* **Résultat** : Objectifs atteints malgré certaines difficultés.

## 10.Appréciation
  **Jeffrey** : Projet enrichissant et complexe, bonne expérience d’apprentissage.
