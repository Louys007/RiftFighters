# 🐉 Analyse du Fonctionnement de RiftFighters

Après avoir exploré l'intégralité du code source du projet `RiftFighters`, voici une synthèse de l'architecture, du code réseau et du moteur de jeu.

---

## 1. Architecture Générale (Pattern MVC/Engine)

Le jeu est découpé de manière très claire pour séparer la logique pure de l'affichage. C'est une condition indispensable pour un mode multijoueur robuste.

*   **`src/CoreEngine/EngineTick.py` (La Logique / Serveur)**
    *   C'est le "cerveau" du jeu. Il tourne à une fréquence fixe (30 Hz) et calcule toute la physique (gravité, sauts), les collisions (entre sprites, obstacles, attaques et boucliers) et la durée des attaques (phases : startup, active, recovery).
    *   Aucun code d'affichage (`pygame.draw` ou `blit`) n'est présent ici.
*   **`src/CoreEngine/EngineRender.py` (L'Affichage / Client Vidéo)**
    *   Dessine les objets interactifs à l'écran. 
    *   Met en place un **système de résolution virtuelle** adaptatif : le jeu simule en permanence un repère global de 1280x720 pixels, et se met à l'échelle (avec *letterboxing* via des bandes noires) en fonction de la taille de la fenêtre de l'utilisateur, gardant les graphismes intacts peu importe l'écran.
*   **`main.py` (L'Orchestrateur Principal)**
    *   Boucle de jeu, instance des interfaces UI (`GameUI`), menus, boutons. 
    *   Gère la boucle de synchronisation des états et *inputs* entre `HOST` et `CLIENT`.

---

## 2. Le Moteur de Combat (`Player.py`)

Chaque joueur/entité repose sur la classe `Player`, une machine à état qui simule la réalité d'un personnage de Versus Fighting :
*   **Mouvements & Dash** : Implémentation du "double-tap" (deux touches rapides dans la direction souhaitée) pour déclencher un *dash* avec ses cooldowns dédiés.
*   **Framedata & Attaques** : Les comportements varient suivant les personnages (Cromagnon = mêlée brutale, Samourai = épée distante, Robot = projectiles). Une attaque obéit à la timeline "Startup" > "Active Hitbox" > "Recovery", typique des moteurs E-Sport.
*   **Défense** : Bouclier (Shield) avec une bulle qui subit une mitigation de dégâts selon `SHIELD_DAMAGE_RATIO`, soumise à un temps de rechargement (`cooldown` de frame) interdisant de bloquer indéfiniment.

---

## 3. L'Architecture Réseau et Netcode Ultra-rapide

C'est là que réside une grande part de la solidité du projet (`src/Network/NetworkManager.py`). Il s'agit d'une architecture **UDP P2P Autorité Serveur avec Prédiction Client et Réconciliation**.

### Comment les joueurs se rencontrent :

1.  **L'Hôte (HOST)** :
    *   Bind un socket en mode `UDP` sur le port `6767`.
    *   S'accorde les autorisations tout seul s'il le faut en invoquant `netsh` via élévation `ctypes` (Pare-feu Windows).
    *   Dialoguel avec le routeur via la bibliothèque `miniupnpc` pour ouvrir dynamiquement un port (UPnP) ! Cela permet aux joueurs de jouer sur internet sans rentrer fastidieusement dans les paramètres de la box.
2.  **Le Client (CLIENT)** :
    *   Bombarde (rafale asynchrone) la cible avec des JSON contenant du texte pur (`{"type": "JOIN"}`) et non plus du `pickle` pour la lisibilité et la sécurité.

### Le Modèle Anti-Lag (Prédiction Client vs Autorité Serveur)

Comment faire en sorte qu'un client qui saute ressente son saut *immédiatement* alors qu'il joue via le réseau ?

*   **Le Client Prédit (`predict_movement`)** : Le joueur 2 appuie sur "Sauter". Son propre navigateur de jeu l'affiche sauter instantanément sans attendre. L'action et la commande (les *inputs*) sont enregistrés dans une file d'attente "en attente" `pending_inputs` horodatée par numéro de séquence `seq`.
*   **L'Hôte Tranche** : L'hôte reçoit cette information "Sauter". L'hôte le fait sauter dans sa simulation Serveur, et lui renvoie son état réel absolu (ses coordonnées `x, y`, sa vie, etc) avec son message reçu en accusé `ack_seq`.
*   **La Réconciliation (`reconcile`)** : Le client reçoit les données absolues du serveur. Le client met à jour ce délai d'imperfection, jette toutes les actions (`pending_inputs`) plus anciennes que l'ack, et replays le reste. Tout ce processus est invisible et masque le ping.

---

## 4. Outils / Évolutions Envisageables

1.  **Routage des Packets** : Le netcode UDP actuellement fait un simple `receive()` local qui cherche la frame la plus récente en vidant le buffer (`recvfrom(4096)` asynchrone). Un petit "Ring Buffer" permettrait de conserver certaines séquences pour interpoler les moments entre 2 paquets si l'un deux se perd (pour les très mauvaises connexions sans fil).
2.  **Audio** : Pas de retour son ! Une bibliothèque Audio (`pygame.mixer`) rendrait l'expérience de combat plus percutante (bruit de coup d'épée, impacts dans le bouclier, menu, musiques).
3.  **OS Indépendant** : L'exclusivité du contournement du pare-feu est uniquement codé sur des APIs Windows PowerShell (`netsh`). Pour adapter le jeu à Linux ou Mac, l'utilisation de `os.name == 'nt'` ou la suppression de cette méthode automatique en faveur de ports toujours pré-ouverts serait souhaitable.
