import pygame
import os
import math
import random

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
        self.stage_name = None
        if background_image:
            self.stage_name = background_image.split(os.sep)[-1] if os.sep in background_image else background_image.split("/")[-1]
            try:
                raw_bg = pygame.image.load(background_image)
                self.background = pygame.transform.scale(raw_bg, (logical_width, logical_height))
            except pygame.error as e:
                print(f"Erreur de chargement de l'image: {e}")
                self.background = None

        # --- Systèmes de Particules (Client-side) ---
        self.hit_particles = []
        self.stage_particles = []
        self._init_stage_particles()

    def _init_stage_particles(self):
        if not self.stage_name: return
        n = self.stage_name.lower()
        if "futur" in n or "lab" in n:
            for _ in range(80):
                self.stage_particles.append([random.randint(0, self.logical_width), random.randint(-500, self.logical_height), random.uniform(5, 15), random.randint(10, 40)])
        elif "cave" in n:
            for _ in range(40):
                self.stage_particles.append([random.randint(0, self.logical_width), random.randint(0, self.logical_height), random.uniform(-1, 1), random.uniform(-1, -2), random.uniform(1, 4)])
        elif "farwest" in n:
            for _ in range(100):
                self.stage_particles.append([random.randint(0, self.logical_width), random.randint(0, self.logical_height), random.uniform(4, 12), random.uniform(-0.5, 0.5), random.uniform(1, 3)])

    def spawn_hit_particles(self, x, y):
        for _ in range(20):
            angle = random.uniform(0, 2*math.pi)
            speed = random.uniform(5, 18)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            color = random.choice([(0, 255, 255), (255, 50, 150), (255, 255, 255), (100, 255, 100)])
            self.hit_particles.append([x, y, vx, vy, random.randint(8, 20), color])

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
        t = pygame.time.get_ticks()
        # 1. Fond statique
        if self.background:
            self.internal_surface.blit(self.background, (0, 0))
        else:
            self.internal_surface.fill((0, 0, 0))
            
        # 1.5. FX de Stage dynamiques
        if self.stage_name:
            n = self.stage_name.lower()
            if "futur" in n or "lab" in n:
                for p in self.stage_particles:
                    p[1] += p[2]
                    if p[1] > self.logical_height:
                        p[1] = -50
                        p[0] = random.randint(0, self.logical_width)
                    pygame.draw.line(self.internal_surface, (0, 255, 255, 100), (p[0], p[1]), (p[0] - p[2]*0.2, p[1] - p[3]), max(1, int(p[2]*0.2)))
            elif "cave" in n:
                for p in self.stage_particles:
                    p[0] += p[2] + math.sin(t*0.001 + p[1])*0.5
                    p[1] += p[3]
                    if p[1] < -20:
                        p[1] = self.logical_height + 20
                        p[0] = random.randint(0, self.logical_width)
                    glow = (math.sin(t*0.005 + p[0]) + 1)/2
                    c = (100, int(150 + 105*glow), 150)
                    pygame.draw.circle(self.internal_surface, (*c, 150), (int(p[0]), int(p[1])), int(p[4]))
            elif "farwest" in n:
                for p in self.stage_particles:
                    p[0] += p[2]
                    p[1] += p[3]
                    if p[0] > self.logical_width:
                        p[0] = -20
                        p[1] = random.randint(0, self.logical_height)
                    pygame.draw.line(self.internal_surface, (200, 150, 50, 100), (p[0], p[1]), (p[0]+p[4]*2, p[1]), max(1, int(p[4]/2)))
                overlay = pygame.Surface((self.logical_width, self.logical_height), pygame.SRCALPHA)
                overlay.fill((255, 150, 0, 20))
                self.internal_surface.blit(overlay, (0, 0))

        # 2. Objets du jeu (joueurs, plateformes)
        for obj in self.objects:
            if hasattr(obj, 'health'):
                last_hp = getattr(obj, "last_rendered_hp", obj.max_health)
                if obj.health < last_hp:
                    # Le joueur a perdu des HP dans la réalité rendue, on éclabousse
                    hw = obj.width * obj.hitbox_width_ratio
                    hh = obj.height * obj.hitbox_height_ratio
                    self.spawn_hit_particles(obj.x + hw, obj.y + hh//2)
                obj.last_rendered_hp = obj.health
                
            obj.render(self)

        # 3. Projectiles par-dessus les objets
        if self.tick_engine:
            self.tick_engine.render_projectiles(self)
            
        # 3.5. Rendu des Particules d'Impact
        for p in self.hit_particles[:]:
            p[0] += p[2]
            p[1] += p[3]
            p[3] += 0.8
            p[4] -= 1
            if p[4] <= 0:
                self.hit_particles.remove(p)
            else:
                progress = p[4] / 20.0
                rad = max(1, int(4 * progress))
                pygame.draw.circle(self.internal_surface, p[5], (int(p[0]), int(p[1])), rad)

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