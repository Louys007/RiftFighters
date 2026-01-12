import pygame


class Player:
    def __init__(self, x, y, color=(200, 50, 50)):
        self.x = x
        self.y = y
        self.width = 50
        self.height = 50
        self.color = color

        # Physique
        self.velocity_y = 0
        self.gravity = 2
        self.speed = 16
        self.jump_strength = -30
        self.on_ground = False

        # Inputs actuels (pour le tick)
        self.inputs = {"left": False, "right": False, "jump": False}

    def update_inputs(self, keys):
        """maj des inputs soit avec pygame, soit avec réseau"""
        self.inputs = keys

    def tick(self):
        if self.inputs["left"] and self.x > 0:  #Le joueur ne peut pas sortir de l'écran à gauche
            self.x -= self.speed
        if self.inputs["right"] and self.x < 800 - self.width:   #Le joueur ne peux pas sortir de l'écran à droite
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
        # seuil = 50px , on peut changer
        # Si < 50, on fait confiance au client
        # Si > 50, le serveur a raison
        if abs(self.x - server_x) > 50 or abs(self.y - server_y) > 50: ## la c'est blanc ou noir mais je pourrait faire une renciliation smooth
            self.x = server_x
            self.y = server_y