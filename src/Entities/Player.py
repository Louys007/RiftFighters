import pygame
import os
from ..Utils.UtilsFunctions import *

class Player:
    def __init__(self, x, y, config):
        """
        config est un dictionnaire contenant :
        {'name': str, 'image': str, 'size': tuple, 'speed': int, 'jump': int, 'gravity': int}
        'image' doit pointer vers le sprite idle, ex: 'cromagnon/cromagnon_idle.png'
        Le sprite walk est déduit automatiquement : 'cromagnon/cromagnon_walk.png'
        """
        self.x = x
        self.y = y
        self.facing_right = True

        wanted_size = config.get('size', None)

        # --- Chargement sprite IDLE ---
        self.sprite_idle = None
        image_path = os.path.join("assets", "Perso", config['image'])

        try:
            loaded_img = pygame.image.load(image_path).convert_alpha()
            if wanted_size is None:
                wanted_size = loaded_img.get_size()
            self.sprite_idle = pygame.transform.scale(loaded_img, wanted_size)
            self.width = self.sprite_idle.get_width()
            self.height = self.sprite_idle.get_height()
        except Exception as e:
            print(f"Erreur chargement idle {image_path}: {e}")
            self.width = 50
            self.height = 50
            self.sprite_idle = None
            self.color = (255, 0, 255)

        # --- Chargement sprite WALK ---
        walk_path = image_path.replace("_idle", "_walk")
        try:
            walk_img = pygame.image.load(walk_path).convert_alpha()
            self.sprite_walk = pygame.transform.scale(walk_img, wanted_size)
        except Exception as e:
            print(f"Erreur chargement walk {walk_path}: {e}")
            self.sprite_walk = self.sprite_idle  # fallback sur idle si pas d'image walk
        
        # --- Chargement sprite JUMP ---
        jump_path = image_path.replace("_idle", "_jump")
        try:
            jump_img = pygame.image.load(jump_path).convert_alpha()
            self.sprite_jump = pygame.transform.scale(jump_img, wanted_size)
        except Exception as e:
            print(f"Erreur chargement jump {jump_path}: {e}")
            self.sprite_jump = self.sprite_idle  # fallback sur idle

        # sprite courant (alias utilisé pour le fallback couleur)
        self.sprite = self.sprite_idle

        # --- Animation ---
        self.anim_timer = 0
        self.anim_interval = 16  # change de sprite toutes les 8 frames (~4x/sec à 30fps)
        self.is_moving = False

        # --- Statistiques depuis la config ---
        self.speed = config.get('speed', 16)
        self.jump_strength = config.get('jump', -30)
        self.gravity = config.get('gravity', 2)

        # --- Physique interne ---
        self.velocity_y = 0
        self.on_ground = False
        self.inputs = {"left": False, "right": False, "jump": False}

        # --- Système de vie ---
        self.max_health = 100
        self.health = self.max_health
        self.is_alive = True

    def take_damage(self, amount):
        """Inflige des dégâts au joueur"""
        if self.is_alive:
            self.health = max(0, self.health - amount)
            if self.health <= 0:
                self.is_alive = False
                self.health = 0

    def heal(self, amount):
        """Soigne le joueur"""
        if self.is_alive:
            self.health = min(self.max_health, self.health + amount)

    def update_inputs(self, keys):
        self.inputs = keys

    def tick(self):
        if not self.is_alive:
            return

        # --- Déplacement ---
        self.is_moving = False

        if self.inputs["left"] and self.x > 0:
            self.x -= self.speed
            self.facing_right = False
            self.is_moving = True

        if self.inputs["right"] and self.x < 1280 - self.width:
            self.x += self.speed
            self.facing_right = True
            self.is_moving = True

        # --- Saut ---
        if self.inputs["jump"] and self.on_ground:
            self.velocity_y = self.jump_strength
            self.on_ground = False

        # --- Timer animation ---
        self.anim_timer += 1
        if self.anim_timer >= self.anim_interval:
            self.anim_timer = 0

        self.apply_gravity()

    def apply_gravity(self):
        self.velocity_y += self.gravity
        self.y += self.velocity_y

    def render(self, RenderEngine):
        if self.sprite_idle:
            # --- Choix du sprite selon l'état ---
            if not self.on_ground:
                image_to_draw = self.sprite_jump
            elif self.is_moving:
                frame = self.anim_timer // (self.anim_interval // 2)
                image_to_draw = self.sprite_walk if frame == 0 else self.sprite_idle
            else:
                image_to_draw = self.sprite_idle

            # --- Flip horizontal si on regarde à gauche ---
            if not self.facing_right:
                image_to_draw = pygame.transform.flip(image_to_draw, True, False)

            # --- Transparence si mort ---
            if not self.is_alive:
                image_to_draw = image_to_draw.copy()
                image_to_draw.set_alpha(100)

            RenderEngine.internal_surface.blit(image_to_draw, (int(self.x), int(self.y)))
        else:
            # Fallback carré de couleur
            color = self.color if self.is_alive else (100, 100, 100)
            RenderEngine.drawCube(self.x, self.y, self.width, self.height, color)

    def reconcile(self, server_x, server_y):
        """Lissage réseau simple"""
        if server_x > self.x:
            self.facing_right = True
        elif server_x < self.x:
            self.facing_right = False

        self.x = lerp(self.x, server_x, 0.2)
        self.y = lerp(self.y, server_y, 0.2)