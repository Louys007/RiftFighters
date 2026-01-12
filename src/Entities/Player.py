import pygame
from ..Utils.UtilsFunctions import *


class Player:
    # Métadonnées pour les menus
    CLASS_NAME = "Unknown"
    MENU_COLOR = (100, 100, 100)

    def __init__(self, x, y, color=None):
        self.x = x
        self.y = y
        self.width = 50
        self.height = 50
        # Utilise la couleur passée en paramètre, sinon celle de la classe
        self.color = color if color else self.MENU_COLOR

        # Physique
        self.velocity_y = 0
        self.gravity = 2
        self.speed = 16
        self.jump_strength = -30
        self.on_ground = False

        # Inputs actuels
        self.inputs = {"left": False, "right": False, "jump": False}

    def update_inputs(self, keys):
        """maj des inputs soit avec pygame, soit avec réseau"""
        self.inputs = keys

    def tick(self):
        if self.inputs["left"] and self.x > 0:
            self.x -= self.speed
        if self.inputs["right"] and self.x < 800 - self.width:
            self.x += self.speed

        if self.inputs["jump"] and self.on_ground:
            self.velocity_y = self.jump_strength
            self.on_ground = False

        self.apply_gravity()

    def apply_gravity(self):
        self.velocity_y += self.gravity
        self.y += self.velocity_y

    def render(self, RenderEngine):
        RenderEngine.drawCube(self.x, self.y, self.width, self.height, self.color)

    def reconcile(self, server_x, server_y):
        smoothing_factor = 0.1
        if abs(server_x - self.x) < 0.1:
            self.x = server_x
        else:
            self.x = lerp(self.x, server_x, smoothing_factor)

        if abs(server_y - self.y) < 0.1:
            self.y = server_y
        else:
            self.y = lerp(self.y, server_y, smoothing_factor)


# --- Sous-classes ---

class CubeFighter(Player):
    CLASS_NAME = "Cube Green"
    MENU_COLOR = (0, 255, 0)

    def __init__(self, x, y, color=None):
        super().__init__(x, y, color)
        self.speed = 16


class RedStriker(Player):
    CLASS_NAME = "Red Striker"
    MENU_COLOR = (255, 50, 50)

    def __init__(self, x, y, color=None):
        super().__init__(x, y, color)
        self.jump_strength = -35  # Saute plus haut
        self.speed = 12  # Moins rapide