```markdown
# 🐉 RiftFighters - Moteur de Combat Multijoueur

Ce projet est un jeu de combat 1v1 en réseau basé sur une architecture **Client-Host avec Prédiction**.
Il inclut désormais un menu complet (Sélection de Stage et de Personnage), un lobby d'attente, et un système de résolution virtuelle adaptative.

> **⚠️ ATTENTION : Windows Uniquement**
> Ce projet utilise des commandes spécifiques à Windows (`netsh`, `ctypes.windll`) pour configurer le pare-feu automatiquement et gérer le mode sans bordure. Il ne fonctionnera pas correctement sur Linux ou MacOS sans modifications.

---

## 📦 Installation

Le moteur nécessite **Pygame** pour l'affichage et **miniupnpc** pour la gestion automatique des ports (UPnP).

```bash
pip install pygame miniupnpc

```

> **Note :** Si l'installation de `miniupnpc` échoue (souvent dû à l'absence de compilateur C++), le jeu se lancera quand même, mais l'ouverture automatique des ports ne fonctionnera pas (vous devrez ouvrir le port 5555 manuellement sur votre box).

---

## 🚀 Comment lancer le jeu

### 1. Lancement

Exécutez la commande suivante dans votre terminal :

```bash
python main.py

```

*Conseil : Lancez votre terminal en **Administrateur** pour que le jeu puisse ouvrir le pare-feu Windows automatiquement lors de l'hébergement d'une partie.*

### 2. Navigation dans les Menus

Le flux de jeu a été amélioré :

1. **Menu Principal :** Choisissez entre **Entraînement** (Solo) ou **Multijoueur**.
2. **Multijoueur :** Choisissez d'**Héberger** ou de **Rejoindre** une IP.
3. **Sélection du Stage :** (Seulement pour le Solo ou l'Hôte) Choisissez l'arène de combat.
4. **Sélection du Personnage :** Choisissez votre combattant (ex: *Cube Green* ou *Red Striker*).
5. **Lobby (Hôte) :** Salle d'attente affichant votre IP publique/locale en attendant que l'adversaire se connecte.

---

## 🖥️ Affichage et Résolution

Le moteur utilise désormais un système de **Résolution Virtuelle** :

* **Résolution Interne :** Le jeu calcule tout en **1280x720 (720p)**.
* **Adaptatif :** Vous pouvez redimensionner la fenêtre à volonté. Le jeu ajoutera automatiquement des bandes noires (letterboxing) pour conserver le ratio d'aspect sans déformer les graphismes.

---

## 🌍 Guide Multijoueur

### 1. Héberger (HOST)

Après avoir choisi votre Stage et Personnage, vous arrivez dans le **Lobby**.

* **IP Locale (LAN) :** À utiliser si votre adversaire est sur le même WiFi.
* **IP Publique (WAN) :** À utiliser si votre adversaire est distant (Internet).
* **Pare-feu :** Le jeu tente d'ouvrir le port **5555** automatiquement. Un bouton dans le lobby permet de forcer l'ouverture du pare-feu Windows si nécessaire.

### 2. Rejoindre (CLIENT)

Entrez l'IP fournie par l'hébergeur. Une fois connecté, choisissez votre personnage pour lancer la partie.

---

## 🛠 Architecture du Moteur

Pour garantir la fluidité et la synchronisation réseau, nous séparons strictement la **Logique** du **Visuel**.

### 1. EngineTick (Le Cerveau)

* **Fichier :** `src/CoreEngine/EngineTick.py`
* **Fréquence :** 30 Hz (Fixe).
* **Rôle :** Physique, déplacements et collisions. C'est la "Vérité" du jeu.
* **Interdit :** Aucun code de dessin (`pygame.draw`) ici.

### 2. EngineRender (Les Yeux)

* **Fichier :** `src/CoreEngine/EngineRender.py`
* **Fréquence :** 30 Hz.
* **Rôle :** Gère la fenêtre, le scaling (mise à l'échelle) et l'affichage des objets.
* **Coordonnées :** Convertit automatiquement les clics de souris de l'écran réel vers la résolution virtuelle.

### 3. MenuSystem (L'Interface)

* **Fichier :** `src/CoreEngine/Menus.py`
* **Rôle :** Gestion de tous les écrans (Main, Stage Select, Char Select, Lobby) et des popups d'erreur.

---

## 👨‍💻 Comment ajouter un Personnage (Guide Dev)

Le système de personnages utilise désormais l'héritage. Pour créer un nouveau combattant :

1. Ouvrez `src/Entities/Player.py`.
2. Créez une classe qui hérite de `Player`.
3. Définissez ses attributs uniques (`CLASS_NAME`, `MENU_COLOR`, vitesse, saut, etc.).

Exemple :

```python
class MonNouveauPerso(Player):
    CLASS_NAME = "Ninja Bleu"
    MENU_COLOR = (0, 0, 255) # Couleur dans le menu
    
    def __init__(self, x, y, color=None):
        super().__init__(x, y, color)
        self.speed = 20        # Plus rapide
        self.jump_strength = -25 # Saute moins haut

```

Il apparaîtra automatiquement dans le menu si vous l'ajoutez à la liste `available_chars` dans `src/CoreEngine/Menus.py`.

---

## 📂 Structure du Projet

```text
main.py                 # Point d'entrée (Gestion taille fenêtre + Boucle jeu)
assets/
└── Stages/             # Images de fond pour les niveaux (.png)
src/
├── CoreEngine/
│   ├── EngineRender.py # Gestion fenêtre, scaling, dessin
│   ├── EngineTick.py   # Physique et collisions
│   └── Menus.py        # Tous les menus et l'UI
│
├── Entities/           
│   ├── Player.py       # Classe Mère Player + Sous-classes (Personnages)
│   └── Platform.py     # Obstacle statique
│
└── Network/            
    └── NetworkManager.py # Sockets, UPnP, Firewall

```

```

```
