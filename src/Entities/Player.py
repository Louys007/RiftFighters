import pygame
import os
from ..Utils.UtilsFunctions import *

class Player:
    def __init__(self, x, y, config):
        """
        config est un dictionnaire contenant : 
        {'name': str, 'image': str, 'speed': int, 'jump': int, 'gravity': int}
        """
        self.x = x
        self.y = y
        
        # --- Chargement de l'image (Taille native) ---
        self.sprite = None
        self.facing_right = True
        
        # On cherche dans assets/Perso/
        image_path = os.path.join("assets", "Perso", config['image'])
        
        try:
            loaded_img = pygame.image.load(image_path).convert_alpha()
            
            # On récupère la taille voulue dans la config, sinon on garde la taille d'origine
            wanted_size = config.get('size', loaded_img.get_size())
            
            self.sprite = pygame.transform.scale(loaded_img, wanted_size)
            self.width = self.sprite.get_width()
            self.height = self.sprite.get_height()

        except Exception as e:
            print(f"Erreur chargement {image_path}: {e}")
            # Fallback : carré rose par défaut si l'image plante
            self.width = 50
            self.height = 50
            self.sprite = None
            self.color = (255, 0, 255)

        # --- Statistiques depuis la config ---
        self.speed = config.get('speed', 16)
        self.jump_strength = config.get('jump', -30)
        self.gravity = config.get('gravity', 2)
        
        # Physique interne
        self.velocity_y = 0
        self.on_ground = False
        self.inputs = {"left": False, "right": False, "jump": False}

    def update_inputs(self, keys):
        self.inputs = keys

    def tick(self):
        # Déplacement
        if self.inputs["left"] and self.x > 0:
            self.x -= self.speed
            self.facing_right = False

        if self.inputs["right"] and self.x < 1280 - self.width:
            self.x += self.speed
            self.facing_right = True

        # Saut
        if self.inputs["jump"] and self.on_ground:
            self.velocity_y = self.jump_strength
            self.on_ground = False

        self.apply_gravity()

    def apply_gravity(self):
        self.velocity_y += self.gravity
        self.y += self.velocity_y

    def render(self, RenderEngine):
        if self.sprite:
            image_to_draw = self.sprite
            # Retourner l'image si on regarde à gauche
            if not self.facing_right:
                image_to_draw = pygame.transform.flip(self.sprite, True, False)
            
            RenderEngine.internal_surface.blit(image_to_draw, (int(self.x), int(self.y)))
        else:
            # Fallback (carré de couleur)
            RenderEngine.drawCube(self.x, self.y, self.width, self.height, self.color)

    def reconcile(self, server_x, server_y):
        # Lissage réseau simple
        if server_x > self.x: self.facing_right = True
        elif server_x < self.x: self.facing_right = False
        
        self.x = lerp(self.x, server_x, 0.2)
        self.y = lerp(self.y, server_y, 0.2)