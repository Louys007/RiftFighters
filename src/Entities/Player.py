import pygame

class Player:
    def __init__(self, x, y):
        self.x = x #gauche droite
        self.y = y #haut bas
        self.speed = 10 #vitesse de deplacement
        self.on_ground = False #est sur le sol ?
        self.jump_strength = -10 #puissance du saut
        self.velocity_y = 0 #vitesse verticale utilisé par la gravité et le saut
        self.gravity = 1 #intensité de la gravité
        self.width = 50
        self.height = 50
        self.color = (200, 50, 50)

    def tick(self):
        self.handle_inputs()
        self.apply_gravity()

    def render(self, RenderEngine):
        RenderEngine.drawCube(self.x,self.y,self.width,self.height,self.color)


    def handle_inputs(self): # gere toutes les inputs de touches
        keys = pygame.key.get_pressed()

        if keys[pygame.K_q]:
            self.x -= self.speed
        if keys[pygame.K_d]:
            self.x += self.speed

        if keys[pygame.K_SPACE] and self.on_ground:
            self.velocity_y = self.jump_strength
            self.on_ground = False

    def apply_gravity(self):
        self.velocity_y += self.gravity
        self.y += self.velocity_y

