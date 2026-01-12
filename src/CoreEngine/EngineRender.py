import pygame


class EngineRender:
    def __init__(self, logical_width, logical_height, title="RiftFighters", background_image=None, window_size=None):
        # 1. Configuration de la fenêtre RÉELLE (redimensionnable)
        self.logical_width = logical_width
        self.logical_height = logical_height

        # Détermination de la taille de départ
        # Si une taille est imposée (ex: taille de l'écran au lancement, ou taille précédente), on l'utilise.
        if window_size:
            win_w, win_h = window_size
        else:
            win_w, win_h = logical_width, logical_height

        # On initialise l'écran en mode redimensionnable avec la taille calculée
        self.screen = pygame.display.set_mode((win_w, win_h), pygame.RESIZABLE)
        pygame.display.set_caption(title)

        # 2. Surface INTERNE (taille fixe 800x600) sur laquelle on dessine tout
        self.internal_surface = pygame.Surface((logical_width, logical_height))

        self.clock = pygame.time.Clock()
        self.objects = []

        # Gestion du scaling (zoom et centrage)
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.update_scale_factors()  # Calcul initial

        # Charger et redimensionner l'image de fond (taille logique)
        self.background = None
        if background_image:
            try:
                raw_bg = pygame.image.load(background_image)
                # On redimensionne l'image pour qu'elle fit parfaitement la résolution logique
                self.background = pygame.transform.scale(raw_bg, (logical_width, logical_height))
            except pygame.error as e:
                print(f"Erreur de chargement de l'image: {e}")
                self.background = None

    def update_scale_factors(self):
        """Recalcule le ratio de zoom et les marges pour garder les proportions (letterboxing)"""
        screen_w, screen_h = self.screen.get_size()

        # On cherche le facteur de zoom max qui rentre dans l'écran sans déborder
        scale_w = screen_w / self.logical_width
        scale_h = screen_h / self.logical_height
        self.scale = min(scale_w, scale_h)

        # Taille finale de l'image une fois zoomée
        new_w = int(self.logical_width * self.scale)
        new_h = int(self.logical_height * self.scale)

        # Calcul des bandes noires (offsets) pour centrer l'image
        self.offset_x = (screen_w - new_w) // 2
        self.offset_y = (screen_h - new_h) // 2

    def get_virtual_mouse_pos(self):
        """Convertit la position réelle de la souris (écran) vers la position virtuelle (jeu 800x600)"""
        mouse_x, mouse_y = pygame.mouse.get_pos()

        # On retire les bandes noires et on divise par le facteur de zoom
        virtual_x = (mouse_x - self.offset_x) / self.scale
        virtual_y = (mouse_y - self.offset_y) / self.scale

        return int(virtual_x), int(virtual_y)

    def add_object(self, obj):
        self.objects.append(obj)

    def drawCube(self, x, y, width, height, color):
        rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.internal_surface, color, rect)

    def render_frame(self):
        # 1. Effacer / Dessiner le fond sur la surface INTERNE (Virtuelle)
        if self.background:
            self.internal_surface.blit(self.background, (0, 0))
        else:
            self.internal_surface.fill((0, 0, 0))

        # 2. Dessiner les objets du jeu sur la surface INTERNE
        for obj in self.objects:
            obj.render(self)

        # 3. UPSCALING : Projeter la surface interne sur l'écran réel
        target_w = int(self.logical_width * self.scale)
        target_h = int(self.logical_height * self.scale)

        scaled_surf = pygame.transform.scale(self.internal_surface, (target_w, target_h))

        self.screen.fill((0, 0, 0))
        self.screen.blit(scaled_surf, (self.offset_x, self.offset_y))

        pygame.display.flip()
        self.clock.tick(60)