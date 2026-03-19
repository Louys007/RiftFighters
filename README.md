```markdown
# 🐉 RiftFighters - Moteur de Combat Multijoueur

Ce projet est un jeu de combat 2D nerveux en réseau basé sur une architecture **Client-Host avec Prédiction Client**, fonctionnant désormais intégralement en **UDP**.

Il inclut un menu complet (Sélection de Mode, de Stage et de Personnage), un système de résolution virtuelle adaptative, et un **netcode ultra-optimisé** sans lag ressenti.

> **⚠️ ATTENTION : Windows Uniquement**
> Ce projet utilise des commandes spécifiques à Windows (`netsh`, `ctypes.windll`) pour configurer le pare-feu automatiquement (UDP) et gérer l'élévation des privilèges. Il ne fonctionnera pas correctement sur Linux ou MacOS sans modifications du module réseau.

---

## 📦 Installation

Le moteur nécessite **Pygame** pour l'affichage, les collisions et l'UI, ainsi que **miniupnpc** pour la gestion automatique de la redirection des ports (UPnP).

```bash
pip install pygame miniupnpc
```

*Note : Si l'installation de `miniupnpc` échoue (souvent dû à l'absence de compilateur C++), le jeu se lancera quand même, mais la redirection automatique du routeur ne fonctionnera pas (vous devrez ouvrir le **port 6767 en UDP** manuellement sur votre box).*

## 🚀 Comment lancer le jeu

### 1. Lancement
Exécutez la commande suivante dans votre terminal :
```bash
python main.py
```
*Conseil : Lancez votre terminal en **Administrateur** pour que le jeu puisse ouvrir le pare-feu Windows automatiquement lors de l'hébergement d'une partie.*

### 2. Navigation dans les Menus
Le flux de jeu propose plusieurs expériences :
* **Menu Principal** : Choisissez entre **Entraînement** ou **Multijoueur**.
* **Entraînement** : Choisissez entre **1v0 (Solo)** pour tester la physique ou **1v1 (Local)** pour jouer à deux sur le même clavier.
* **Multijoueur** : Choisissez d'**Héberger (Host)** ou de **Rejoindre (Client)** une IP.
* **Sélection du Stage** : (Seulement pour le Solo ou l'Hôte) Choisissez l'arène de combat.
* **Sélection du Personnage** : Choisissez votre combattant (ex: **Cromagnon** (Mêlée) ou **Robot** (Distance)).

## 🖥️ Affichage et Résolution

Le moteur utilise un système de **Résolution Virtuelle** :
* **Résolution Interne** : Le jeu calcule toute la logique et les graphismes en **1280x720 (720p)**.
* **Adaptatif** : Vous pouvez redimensionner la fenêtre à volonté. Le jeu ajoutera automatiquement des bandes noires (letterboxing) pour conserver le ratio d'aspect parfait sans jamais déformer les graphismes.

## 🌍 Guide Multijoueur & Netcode

Le jeu utilise désormais un **Netcode Esport** ultra-performant. 

### 1. Héberger (HOST)
Après avoir choisi votre Stage et Personnage, le jeu prépare le terrain :
* **Pare-feu & Box** : Le jeu tente d'ouvrir le port **6767 (UDP)** automatiquement sur Windows (`netsh`) et sur votre box Internet (`UPnP`).
* **IP Locale (LAN)** : À utiliser si votre adversaire est sur le même WiFi.
* **IP Publique (WAN)** : À utiliser si votre adversaire est distant (Internet).

### 2. Rejoindre (CLIENT)
Entrez l'IP fournie par l'hébergeur. Le jeu enverra des requêtes de connexion (`JOIN`) de manière asynchrone jusqu'à ce que l'hôte accepte.

### ⚡ Les Optimisations Réseau (Nouveau !)
* **UDP au lieu de TCP** : Les paquets sont envoyés en rafale sans bloquer le jeu. Fini les "freezes" d'écran lorsqu'un paquet se perd sur Internet.
* **Sécurité JSON** : Les données transitent en texte pur `JSON` (numéro de séquence, touches pressées, position), remplaçant l'ancien système `pickle` qui posait des risques de sécurité.
* **Prédiction Client & Réconciliation** : Le mouvement du client est simulé instantanément sur son propre écran (zéro délai/lag). Quand le serveur envoie la "vraie" position, le client se corrige de manière invisible et rejoue ses dernières touches. *Adieu l'effet élastique (rubber-banding) !*

## 🛠 Architecture du Moteur

Pour garantir la fluidité et la synchronisation réseau, nous séparons strictement la **Logique** du **Visuel**.

### 1. EngineTick (Le Cerveau)
* **Fichier** : `src/CoreEngine/EngineTick.py`
* **Fréquence** : 30 Hz (Fixe).
* **Rôle** : Gère la physique, les déplacements, l'anti-traversée, les attaques, les projectiles et les collisions. C'est la "Vérité" absolue du jeu.
* **Interdit** : Aucun code de dessin (`pygame.draw`) n'est présent ici.

### 2. EngineRender (Les Yeux)
* **Fichier** : `src/CoreEngine/EngineRender.py`
* **Fréquence** : 30 FPS.
* **Rôle** : Gère la fenêtre, le scaling (mise à l'échelle), l'UI (GameUI) et le rendu final des entités.
* **Coordonnées** : Convertit automatiquement les clics de souris de l'écran réel vers la résolution virtuelle.

### 3. MenuSystem (L'Interface)
* **Fichier** : `src/CoreEngine/Menus.py`
* **Rôle** : Gestion de la machine à états des écrans (Main, Stage Select, Char Select, Solo Type), des previews en cache et des popups d'erreur.

---

## 📂 Structure du Projet

```text
main.py                 # Point d'entrée (Gestion taille fenêtre + Boucle de jeu + Synchro Réseau)
assets/
└── Stages/             # Images de fond pour les niveaux (.png)
src/
├── CoreEngine/
│   ├── EngineRender.py # Gestion fenêtre, scaling, dessin
│   ├── EngineTick.py   # Physique, attaques, projectiles et collisions
│   └── Menus.py        # Tous les menus et l'UI
│
├── Entities/           
│   ├── Player.py       # Classe Player (Logique des personnages, Prédiction/Réconciliation)
│   └── Platform.py     # Obstacles statiques (Sol)
│
└── Network/                
    └── NetworkManager.py # Sockets UDP, Séquençage JSON, UPnP, Firewall Windows
```
```