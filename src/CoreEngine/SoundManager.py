"""
SoundManager.py
===============
Gestion centralisée des sons pour RiftFighters.

Structure réelle dans assets/Sounds/ :
  Click-Select.wav
  Bouclier.wav
  Damage-taken.wav
  Dash.wav
  cromagnon/
    Spear-Throw.wav          → attack2 (lancer de lance)
  robot/
    attack1.wav
    attack2.wav
  samourai/
    attack1.wav
    attack2.wav
  chevalier/                 → vide pour l'instant

API :
  sfx = SoundManager()
  sfx.play("click")
  sfx.play("shield")
  sfx.play("damage")
  sfx.play("dash")
  sfx.play_for("Cromagnon", "attack2")   → Spear-Throw.wav
  sfx.play_for("Robot", "attack1")       → robot/attack1.wav
"""

import pygame
import os

# Racine du projet
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SOUNDS_DIR = os.path.join(_PROJECT_ROOT, "assets", "Sounds")


class SoundManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._sounds = {}
        self._enabled = True

        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            except Exception as e:
                print(f"[SoundManager] Mixer init failed: {e}")
                self._enabled = False
                return

        self._load_all()

    def _load_all(self):
        # --- Sons globaux à la racine de Sounds/ ---
        global_files = {
            "click":    "Click-Select.wav",
            "shield":   "Bouclier.wav",
            "damage":   "Damage-taken.wav",
            "dash":     "Dash.wav",
        }
        for key, filename in global_files.items():
            self._load(key, os.path.join(SOUNDS_DIR, filename))

        # --- Sons par personnage ---
        # Format : (clé interne, chemin relatif depuis SOUNDS_DIR)
        per_char = [
            # Cromagnon
            ("cromagnon_attack2", os.path.join("cromagnon", "Spear-Throw.wav")),
            # Robot
            ("robot_attack1",     os.path.join("robot",     "attack1.wav")),
            ("robot_attack2",     os.path.join("robot",     "attack2.wav")),
            # Samourai
            ("samourai_attack1",  os.path.join("samourai",  "attack1.wav")),
            ("samourai_attack2",  os.path.join("samourai",  "attack2.wav")),
            # Chevalier (vide pour l'instant — sera ajouté au fur et à mesure)
        ]
        for key, rel_path in per_char:
            self._load(key, os.path.join(SOUNDS_DIR, rel_path))

    def _load(self, key: str, path: str):
        try:
            if os.path.exists(path):
                self._sounds[key] = pygame.mixer.Sound(path)
        except Exception as e:
            print(f"[SoundManager] Erreur {path}: {e}")

    # ------------------------------------------------------------------ #
    #  API PUBLIQUE
    # ------------------------------------------------------------------ #

    def play(self, name: str, volume: float = 1.0):
        """Joue un son global : 'click', 'shield', 'damage', 'dash'."""
        if not self._enabled:
            return
        sound = self._sounds.get(name)
        if sound:
            sound.set_volume(volume)
            sound.play()

    def play_for(self, character_name: str, sound_name: str, volume: float = 1.0):
        """
        Joue un son lié à un personnage.
        character_name : "Cromagnon", "Robot", "Samourai", "Chevalier"
        sound_name     : "attack1", "attack2", "hurt"
        """
        if not self._enabled:
            return
        key   = f"{character_name.lower()}_{sound_name}"
        sound = self._sounds.get(key)
        if sound:
            sound.set_volume(volume)
            sound.play()
        # Si le son n'existe pas (chevalier vide, cromagnon attack1 absent) → silencieux

    def add_sound(self, key: str, path: str):
        """Permet d'ajouter un son après l'initialisation (quand les fichiers arrivent)."""
        self._load(key, path)

    def set_enabled(self, enabled: bool):
        self._enabled = enabled
        if not enabled:
            pygame.mixer.stop()