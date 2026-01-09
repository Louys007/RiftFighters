```markdown
# 🐉 RiftFighters - Moteur de Combat Multijoueur

Ce projet est un jeu de combat 1v1 en réseau basé sur une architecture **Client-Host avec Prédiction**.
Il inclut désormais un menu graphique, un lobby d'attente et une configuration réseau automatique.

> **⚠️ ATTENTION : Windows Uniquement**
> Ce projet utilise des commandes spécifiques à Windows (`netsh`, `ctypes.windll`) pour configurer le pare-feu automatiquement. Il ne fonctionnera pas sur Linux ou MacOS sans modifications.

---

## 📦 Installation

Le moteur nécessite **Pygame** pour l'affichage et **miniupnpc** pour la gestion automatique des ports (UPnP).

```bash
pip install pygame miniupnpc

```

> **Note :** Si l'installation de `miniupnpc` échoue (souvent dû à l'absence de compilateur C++), le jeu se lancera quand même, mais l'ouverture automatique des ports ne fonctionnera pas.

---

## 🚀 Comment lancer le jeu

1. **Lancement :**
Exécutez la commande suivante dans votre terminal :
```bash
python main.py

```


*Conseil : Lancez votre terminal en **Administrateur** pour que le jeu puisse ouvrir le pare-feu Windows automatiquement.*
2. **Menu Principal :**
* **Entraînement :** Pour tester les déplacements seul.
* **Multijoueur :** Pour accéder au lobby réseau.



---

## 🌍 Guide Multijoueur

### 1. Héberger (HOST)

Dans le menu Multijoueur, cliquez sur **Héberger**. Vous arriverez dans le Lobby qui affiche deux informations :

* **IP Locale (LAN) :** À utiliser si votre adversaire est sur le même WiFi.
* **IP Publique (WAN) :** À utiliser si votre adversaire est distant (Internet).

> **Automatisme :** Le jeu tente d'ouvrir le port **5555** sur votre Box (via UPnP) et sur votre PC (via le Pare-feu Windows).

### 2. Rejoindre (CLIENT)

Cliquez sur **Rejoindre**, entrez l'IP fournie par l'hébergeur dans la case prévue, et validez.

---

## 🛠 Architecture du Moteur

Pour garantir la fluidité, nous séparons strictement la **Logique** du **Visuel**.

### 1. EngineTick (Le Cerveau)

* **Fichier :** `src/CoreEngine/EngineTick.py`
* **Fréquence :** 60 Hz (Fixe).
* **Rôle :** Physique et collisions ("La Vérité").
* **Interdit :** Aucun code de dessin (`pygame.draw`) ici.

### 2. EngineRender (Les Yeux)

* **Fichier :** `src/CoreEngine/EngineRender.py`
* **Fréquence :** FPS illimité.
* **Rôle :** Interpolation et affichage des objets.

### 3. MenuSystem (L'Interface)

* **Fichier :** `src/CoreEngine/Menus.py`
* **Rôle :** Gestion des écrans, boutons, champs textes et de la navigation avant le jeu.

### 4. NetworkManager (Le Facteur)

* **Fichier :** `src/Network/NetworkManager.py`
* **Rôle :** Sockets, UPnP, Pare-feu et sérialisation.

---

## 👨‍💻 Comment ajouter un Objet (Guide Dev)

Votre classe doit respecter la séparation Tick/Render :

```python
class MaNouvelleEntite:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.inputs = {"left": False} 

    # --- LOGIQUE (Tick) ---
    def update_inputs(self, keys):
        # OBLIGATOIRE : Permet au réseau de piloter l'entité
        self.inputs = keys

    def tick(self):
        if self.inputs["left"]: self.x -= 5

    # --- VISUEL (Render) ---
    def render(self, engine_render):
        engine_render.drawCube(self.x, self.y, 50, 50, (255, 0, 0))

```

---

## 📂 Structure du Projet

```text
main.py                 # Point d'entrée (Boucle principale)
src/
├── CoreEngine/
│   ├── EngineRender.py # Gestion fenêtre et dessin
│   ├── EngineTick.py   # Physique et collisions
│   └── Menus.py        # UI, Boutons, InputBox
│
├── Entities/           # OBJETS DU JEU
│   ├── Player.py       # Joueur (Physique + Réseau)
│   └── Platform.py     # Obstacle statique
│
└── Network/            
    └── NetworkManager.py # Sockets, UPnP, Firewall (WinOnly)

```

```

```
