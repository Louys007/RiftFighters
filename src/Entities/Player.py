import pygame
from ..Utils.UtilsFunctions import *

class Player:
    def __init__(self, x, y, color=(200, 50, 50)):
        self.x = x
        self.y = y
        self.width = 50
        self.height = 50
        self.color = color

        # Physique
        self.velocity_y = 0
        self.gravity = 1
        self.speed = 10
        self.jump_strength = -15
        self.on_ground = False

        # Inputs actuels (pour le tick)
        self.inputs = {"left": False, "right": False, "jump": False}

    def update_inputs(self, keys):
        """maj des inputs soit avec pygame, soit avec réseau"""
        self.inputs = keys

    def tick(self):
        if self.inputs["left"]:
            self.x -= self.speed
        if self.inputs["right"]:
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
        """force la position si l'écart est trop grand souvent a cause du lag vu qu'il ny aura pas de cheater"""

        # plus c'est proche de 1 plus ca sera rapide et sec (potentiellement laggy) et plus c'est loin de 1 plus ca sera long et smooth (en retard)
        smoothing_factor = 0.1 # compris entre 0 et 1

        if abs(server_x - self.x) < 0.1: # snap si on est vraiment proche
            self.x = server_x

        else:
            self.x = lerp(self.x, server_x, smoothing_factor) # smooth sinon

        if abs(server_y - self.y) < 0.1: # snap si on est vraiment proche
            self.y = server_y
        else:
            self.y = lerp(self.y, server_y, smoothing_factor) # smooth sinon


