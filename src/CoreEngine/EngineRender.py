import pygame


class EngineRender:
    def __init__(self, logical_width, logical_height, title="RiftFighters", background_image=None, window_size=None):
        self.logical_width = logical_width
        self.logical_height = logical_height

        if window_size:
            win_w, win_h = window_size
        else:
            win_w, win_h = logical_width, logical_height

        self.screen = pygame.display.set_mode((win_w, win_h), pygame.RESIZABLE)
        pygame.display.set_caption(title)

        self.internal_surface = pygame.Surface((logical_width, logical_height))

        self.clock = pygame.time.Clock()
        self.objects = []

        # HUD (GameUI)
        self.hud = None

        # EngineTick (pour le rendu des projectiles)
        self.tick_engine = None

        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.update_scale_factors()

        self.background = None
        if background_image:
            try:
                raw_bg = pygame.image.load(background_image)
                self.background = pygame.transform.scale(raw_bg, (logical_width, logical_height))
            except pygame.error as e:
                print(f"Erreur de chargement de l'image: {e}")
                self.background = None

    def set_hud(self, game_ui):
        """Enregistre le HUD (GameUI)"""
        self.hud = game_ui

    def set_tick_engine(self, tick_engine):
        """Enregistre le tick engine pour le rendu des projectiles"""
        self.tick_engine = tick_engine

    def update_scale_factors(self):
        """Recalcule le ratio de zoom et les marges (letterboxing)"""
        screen_w, screen_h = self.screen.get_size()
        scale_w = screen_w / self.logical_width
        scale_h = screen_h / self.logical_height
        self.scale = min(scale_w, scale_h)

        new_w = int(self.logical_width * self.scale)
        new_h = int(self.logical_height * self.scale)

        self.offset_x = (screen_w - new_w) // 2
        self.offset_y = (screen_h - new_h) // 2

    def get_virtual_mouse_pos(self):
        """Convertit la position souris écran → position virtuelle jeu"""
        mouse_x, mouse_y = pygame.mouse.get_pos()
        virtual_x = (mouse_x - self.offset_x) / self.scale
        virtual_y = (mouse_y - self.offset_y) / self.scale
        return int(virtual_x), int(virtual_y)

    def add_object(self, obj):
        self.objects.append(obj)

    def drawCube(self, x, y, width, height, color):
        rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.internal_surface, color, rect)

    def render_frame(self):
        # 1. Fond
        if self.background:
            self.internal_surface.blit(self.background, (0, 0))
        else:
            self.internal_surface.fill((0, 0, 0))

        # 2. Objets du jeu (joueurs, plateformes)
        for obj in self.objects:
            obj.render(self)

        # 3. Projectiles par-dessus les objets
        if self.tick_engine:
            self.tick_engine.render_projectiles(self)

        # 4. HUD par-dessus tout (timer, barres de vie, game over)
        if self.hud:
            self.hud.render(self.internal_surface)

        # 5. Upscaling + projection sur l'écran réel + flip unique
        target_w = int(self.logical_width * self.scale)
        target_h = int(self.logical_height * self.scale)
        scaled_surf = pygame.transform.scale(self.internal_surface, (target_w, target_h))

        self.screen.fill((0, 0, 0))
        self.screen.blit(scaled_surf, (self.offset_x, self.offset_y))

        pygame.display.flip()
        self.clock.tick(30)