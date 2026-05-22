"""
KeyBindings.py
==============
Gestion centralisée des touches pour les deux joueurs.
- Chargement / sauvegarde automatique dans keybindings.json
- Valeurs par défaut incluses
- Fournit get_inputs_p1() / get_inputs_p2() prêts à l'emploi pour main.py
"""

import json
import os
import pygame

# Chemin du fichier de sauvegarde (à la racine du projet)
SAVE_PATH = "keybindings.json"

# Actions disponibles pour chaque joueur
ACTIONS = ["left", "right", "jump", "attack", "attack2", "shield"]

# Labels affichés dans le menu de configuration
ACTION_LABELS = {
    "left":    "Aller à gauche",
    "right":   "Aller à droite",
    "jump":    "Sauter",
    "attack":  "Attaque 1",
    "attack2": "Attaque 2",
    "shield":  "Bouclier",
}

# Touches par défaut — touches pygame (int)
DEFAULT_BINDINGS = {
    "p1": {
        "left":    pygame.K_q,
        "right":   pygame.K_d,
        "jump":    pygame.K_SPACE,
        "attack":  pygame.K_g,
        "attack2": pygame.K_h,
        "shield":  pygame.K_n,
    },
    "p2": {
        "left":    pygame.K_LEFT,
        "right":   pygame.K_RIGHT,
        "jump":    pygame.K_UP,
        "attack":  pygame.K_RETURN,
        "attack2": pygame.K_RSHIFT,
        "shield":  pygame.K_m,
    }
}


def _load() -> dict:
    """Charge depuis le JSON ou retourne les défauts."""
    if os.path.exists(SAVE_PATH):
        try:
            with open(SAVE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            # Validation : s'assure que toutes les actions existent
            for player in ("p1", "p2"):
                if player not in data:
                    data[player] = dict(DEFAULT_BINDINGS[player])
                for action in ACTIONS:
                    if action not in data[player]:
                        data[player][action] = DEFAULT_BINDINGS[player][action]
                    else:
                        data[player][action] = int(data[player][action])
            return data
        except Exception:
            pass
    # Fichier absent ou corrompu → défauts
    return {
        "p1": dict(DEFAULT_BINDINGS["p1"]),
        "p2": dict(DEFAULT_BINDINGS["p2"]),
    }


def _save(bindings: dict):
    """Sauvegarde les bindings dans le JSON."""
    try:
        with open(SAVE_PATH, "w", encoding="utf-8") as f:
            json.dump(bindings, f, indent=2)
    except Exception as e:
        print(f"[KeyBindings] Erreur sauvegarde : {e}")


# -----------------------------------------------------------------------
# Singleton en mémoire (chargé une fois au premier import)
# -----------------------------------------------------------------------
_bindings: dict = _load()


def get(player: str, action: str) -> int:
    """Retourne le keycode pygame pour (player='p1'/'p2', action)."""
    return _bindings[player][action]


def set_key(player: str, action: str, keycode: int):
    """Modifie une touche et sauvegarde immédiatement."""
    _bindings[player][action] = keycode
    _save(_bindings)


def reset_defaults():
    """Remet toutes les touches aux valeurs par défaut et sauvegarde."""
    global _bindings
    _bindings = {
        "p1": dict(DEFAULT_BINDINGS["p1"]),
        "p2": dict(DEFAULT_BINDINGS["p2"]),
    }
    _save(_bindings)


def get_all() -> dict:
    """Retourne une copie complète des bindings actuels."""
    return {
        "p1": dict(_bindings["p1"]),
        "p2": dict(_bindings["p2"]),
    }


def key_name(keycode: int) -> str:
    """Retourne un nom lisible pour une touche pygame."""
    name = pygame.key.name(keycode)
    # Améliore quelques noms peu lisibles
    replacements = {
        "return":      "ENTRÉE",
        "space":       "ESPACE",
        "left shift":  "MAJ G",
        "right shift": "MAJ D",
        "left ctrl":   "CTRL G",
        "right ctrl":  "CTRL D",
        "left alt":    "ALT G",
        "right alt":   "ALT D",
        "up":          "↑",
        "down":        "↓",
        "left":        "←",
        "right":       "→",
        "backspace":   "RETOUR",
        "tab":         "TAB",
        "escape":      "ÉCHAP",
        "delete":      "SUPPR",
    }
    return replacements.get(name.lower(), name.upper())


# -----------------------------------------------------------------------
# Helpers pour main.py
# -----------------------------------------------------------------------

def get_inputs_p1() -> dict:
    """Retourne le dict d'inputs P1 à partir de l'état courant du clavier."""
    k = pygame.key.get_pressed()
    b = _bindings["p1"]
    return {
        "left":    bool(k[b["left"]]),
        "right":   bool(k[b["right"]]),
        "jump":    bool(k[b["jump"]]),
        "attack":  bool(k[b["attack"]]),
        "attack2": bool(k[b["attack2"]]),
        "shield":  bool(k[b["shield"]]),
    }


def get_inputs_p2() -> dict:
    """Retourne le dict d'inputs P2 à partir de l'état courant du clavier."""
    k = pygame.key.get_pressed()
    b = _bindings["p2"]
    return {
        "left":    bool(k[b["left"]]),
        "right":   bool(k[b["right"]]),
        "jump":    bool(k[b["jump"]]),
        "attack":  bool(k[b["attack"]]),
        "attack2": bool(k[b["attack2"]]),
        "shield":  bool(k[b["shield"]]),
    }