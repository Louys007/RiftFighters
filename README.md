# 🐉 RiftFighters - Moteur de Combat Multijoueur

Ce projet est un jeu de combat 1v1 en réseau basé sur une architecture **Client-Host avec Prédiction**.

> **⚠️ Note pour l'équipe :** Le système multijoueur est complexe (Synchronisation, Lag compensation, Sockets). **Vous n'avez pas besoin de toucher au dossier `src/Network/`.**
> Si vous respectez la structure `Tick` (Logique) vs `Render` (Visuel) décrite ci-dessous, le multijoueur fonctionnera "magiquement" avec vos objets.

---

## 🚀 Comment lancer le jeu

Le jeu nécessite deux instances pour fonctionner (un Hébergeur et un Joueur).

1. **Lancez le Host (Serveur + Joueur 1)**
* Ouvrez un terminal.
* Tapez : `python main.py`
* Choisissez : `h` (Host).


2. **Lancez le Client (Joueur 2)**
* Ouvrez un deuxième terminal.
* Tapez : `python main.py`
* Choisissez : `j` (Join).
* IP : Tapez `localhost` (ou l'IP locale du host).



---

## 🛠 Architecture du Moteur

Pour que le jeu soit fluide même avec du lag, nous séparons strictement la **Logique** du **Visuel**.

### 1. EngineTick (Le Cerveau)

* **Fichier :** `src/CoreEngine/EngineTick.py`
* **Fréquence :** 60 fois par seconde (Fixe).
* **Rôle :** Gère la physique, les collisions, les dégâts.
* **Règle :** C'est ici que la "Vérité" du jeu est calculée.
* **⚠️ Interdit :** Ne jamais mettre de code d'affichage (`pygame.draw`, `blit`) dans une méthode `tick()`.

### 2. EngineRender (Les Yeux)

* **Fichier :** `src/CoreEngine/EngineRender.py`
* **Fréquence :** Aussi vite que l'écran le permet (FPS illimité).
* **Rôle :** Dessine les objets à l'écran.
* **Règle :** Ne fait aucun calcul physique. Il prend juste `x` et `y` et dessine.

---

## 👨‍💻 Comment ajouter un Objet / Perso (Guide Dev)

Pour créer une nouvelle entité (ex: `Fireball`, `NewCharacter`), votre classe doit ressembler à ça :

```python
class MaNouvelleEntite:
    def __init__(self, x, y):
        # Données Physiques (La Vérité)
        self.x = x
        self.y = y
        self.rect = pygame.Rect(x, y, 50, 50)
        
        # Inputs (Ce que l'entité veut faire)
        self.inputs = {"left": False, "right": False} 

    # --- PARTIE LOGIQUE (Tick) ---
    def update_inputs(self, keys):
        """
        Fonction OBLIGATOIRE pour les objets contrôlables.
        Ne lisez JAMAIS pygame.key.get_pressed() directement dans tick() !
        Le réseau va appeler cette fonction pour injecter les touches de l'adversaire.
        """
        self.inputs = keys

    def tick(self):
        """
        Appelé 60 fois/sec. Calculez la nouvelle position ici.
        """
        if self.inputs["left"]:
            self.x -= 5
        
        # Mettre à jour les collisions ici
        self.rect.topleft = (self.x, self.y)

    # --- PARTIE VISUELLE (Render) ---
    def render(self, engine_render):
        """
        Appelé par la boucle de rendu. Dessinez juste l'objet.
        """
        # engine_render contient les méthodes pour dessiner
        engine_render.drawCube(self.x, self.y, 50, 50, (255, 0, 0))

```

### 🛑 Les 3 Règles d'Or à respecter

1. **Séparez Tick et Render :**
* Calculs de positions -> `tick()`
* Dessins `pygame` -> `render()`


2. **Pas d'Input Direct :**
* N'utilisez jamais `pygame.key.get_pressed()` à l'intérieur de `tick()`.
* Passez toujours par une variable (ex: `self.inputs`) qui est remplie depuis l'extérieur. (Sinon, le serveur ne pourra pas contrôler le personnage du client).


3. **Déterminisme :**
* Si je donne les mêmes inputs, `tick()` doit toujours donner le même résultat. Evitez `random` qui désynchronise le jeu, sauf si c'est purement visuel (particules).



---

## 📂 Structure du Projet

```text
main.py                 # Point d'entrée (Boucle principale)
src/
├── CoreEngine/
│   ├── EngineRender.py # Gestion de la fenêtre et du dessin
│   └── EngineTick.py   # Gestion de la liste des objets et updates
│
├── Entities/           # C'EST ICI QUE VOUS TRAVAILLEZ
│   ├── Player.py       # Exemple de joueur compatible réseau
│   └── Platform.py     # Exemple d'obstacle statique
│
└── Network/            # ⛔ NE PAS TOUCHER (Cerveau du multijoueur)
    └── NetworkManager.py

```

---

## 📚 Bibliothèques

* **pygame** : `pip install pygame`
