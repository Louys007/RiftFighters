import pygame

class EngineRender:
    def __init__(self, width, height,title="RiftFighters", background_image=None):
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption(title)
        self.clock = pygame.time.Clock()
        self.objects = [] # liste des objets a afficher a l'ecran chaque frame

        self.width = width
        self.height = height
        
        # Charger et redimensionner l'image de fond
        self.background = None
        if background_image:
            try:
                self.background = pygame.image.load(background_image)
                # Redimensionner pour remplir l'écran
                self.background = pygame.transform.scale(self.background, (width, height))
            except pygame.error as e:
                print(f"Erreur de chargement de l'image: {e}")
                self.background = None

    def add_object(self,obj):
        self.objects.append(obj)

    def drawCube(self,x,y,width,height,color):
        rect = pygame.Rect(x,y,width,height)
        pygame.draw.rect(self.screen,color,rect)

    def render_frame(self):
        # Afficher le fond (image ou noir)
        if self.background:
            self.screen.blit(self.background, (0, 0))
        else:
            self.screen.fill((0, 0, 0))

        for obj in self.objects:
            obj.render(self)

        pygame.display.flip()
        self.clock.tick(30) # 30 fps