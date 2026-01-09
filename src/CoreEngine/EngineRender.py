import pygame

class EngineRender:
    def __init__(self, width, height, title="RiftFighters"):
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption(title)
        self.clock = pygame.time.Clock()
        self.objects = [] # liste des objets a afficher a l'ecran chaque frame

    def add_object(self,obj):
        self.objects.append(obj)

    def drawCube(self,x,y,width,height,color):
        rect = pygame.Rect(x,y,width,height)
        pygame.draw.rect(self.screen,color,rect)

    def render_frame(self):
        self.screen.fill((0,0,0))
        for obj in self.objects:
            obj.render(self)

        pygame.display.flip()
        self.clock.tick(60) # 60 fps