"""
Projectile.py
=============
Trois types de projectiles selon le personnage :

  RobotProjectile   — boule d'énergie animée (2 frames), trajectoire rectiligne
  LanceProjectile   — lance du Cromagnon, trajectoire parabolique (arc vers le bas)
  ShurikenProjectile— shuriken du Samourai, rotation sur lui-même, trajectoire rectiligne rapide

Chaque classe expose les mêmes attributs/méthodes publiques :
  .active  .hitbox  .tick()  .render(render_engine)  .DAMAGE  .owner
"""

import pygame
import os
import math


# -----------------------------------------------------------------------
# Classe de base
# -----------------------------------------------------------------------

class _BaseProjectile:
    DAMAGE = 0
    SIZE   = (60, 60)

    def __init__(self, x, y, direction, owner):
        self.x         = float(x)
        self.y         = float(y)
        self.direction = direction   # +1 droite, -1 gauche
        self.owner     = owner
        self.active    = True
        self.width     = self.SIZE[0]
        self.height    = self.SIZE[1]

    @property
    def hitbox(self):
        margin = 12
        return pygame.Rect(
            int(self.x) + margin,
            int(self.y) + margin,
            self.width  - margin * 2,
            self.height - margin * 2,
        )

    def _out_of_screen(self):
        return self.x < -self.width - 20 or self.x > 1300

    def tick(self):
        raise NotImplementedError

    def render(self, render_engine):
        raise NotImplementedError


# -----------------------------------------------------------------------
# Robot — boule d'énergie (inchangée)
# -----------------------------------------------------------------------

class RobotProjectile(_BaseProjectile):
    SPEED  = 26
    DAMAGE = 18
    SIZE   = (60, 60)
    ANIM_INTERVAL = 6

    def __init__(self, x, y, direction, owner):
        super().__init__(x, y, direction, owner)
        self.sprites = []
        for i in range(1, 3):
            path = os.path.join("assets", "Perso", "robot", "projo", f"projo_{i}.png")
            try:
                img = pygame.image.load(path).convert_alpha()
                self.sprites.append(pygame.transform.scale(img, self.SIZE))
            except Exception:
                surf = pygame.Surface(self.SIZE, pygame.SRCALPHA)
                surf.fill((0, 200, 255))
                self.sprites.append(surf)
        self.anim_timer = 0

    def tick(self):
        self.x += self.direction * self.SPEED
        self.anim_timer = (self.anim_timer + 1) % (self.ANIM_INTERVAL * len(self.sprites))
        if self._out_of_screen():
            self.active = False

    def render(self, render_engine):
        if not self.active:
            return
        frame = (self.anim_timer // self.ANIM_INTERVAL) % len(self.sprites)
        img = self.sprites[frame]
        if self.direction < 0:
            img = pygame.transform.flip(img, True, False)
        render_engine.internal_surface.blit(img, (int(self.x), int(self.y)))


# -----------------------------------------------------------------------
# Cromagnon — lance parabolique
# -----------------------------------------------------------------------

class LanceProjectile(_BaseProjectile):
    SPEED_X  = 20
    GRAVITY  = 0.45
    DAMAGE   = 14
    SIZE     = (180, 80)  # moins longue qu'avant

    def __init__(self, x, y, direction, owner):
        super().__init__(x, y, direction, owner)
        self.vy      = -7.0        # élan vers le haut plus marqué au départ
        self.angle   = 0.0         # angle d'affichage (suit la trajectoire)

        path = os.path.join("assets", "Perso", "cromagnon", "projo", "projo_lance.png")
        try:
            img = pygame.image.load(path).convert_alpha()
            self._sprite_base = pygame.transform.scale(img, self.SIZE)
        except Exception:
            surf = pygame.Surface(self.SIZE, pygame.SRCALPHA)
            pygame.draw.polygon(surf, (200, 150, 80),
                                [(0, self.SIZE[1]//2), (self.SIZE[0], self.SIZE[1]//2 - 6),
                                 (self.SIZE[0], self.SIZE[1]//2 + 6)])
            self._sprite_base = surf

        # On pré-flip si on tire vers la gauche
        if direction < 0:
            self._sprite_base = pygame.transform.flip(self._sprite_base, True, False)

    def tick(self):
        # Physique parabolique
        self.vy  += self.GRAVITY
        self.x   += self.direction * self.SPEED_X
        self.y   += self.vy

        # Angle visuel : arctan de la vitesse (la lance pointe dans sa direction de vol)
        angle_rad  = math.atan2(self.vy, self.SPEED_X)
        self.angle = math.degrees(angle_rad) * self.direction   # miroir pour la gauche

        if self._out_of_screen() or self.y > 800:
            self.active = False

    def render(self, render_engine):
        if not self.active:
            return
        rotated = pygame.transform.rotate(self._sprite_base, -self.angle)
        cx = int(self.x) + self.width  // 2
        cy = int(self.y) + self.height // 2
        render_engine.internal_surface.blit(rotated, (cx - rotated.get_width() // 2,
                                                       cy - rotated.get_height() // 2))


# -----------------------------------------------------------------------
# Samourai — shuriken rotatif
# -----------------------------------------------------------------------

class ShurikenProjectile(_BaseProjectile):
    SPEED      = 24
    ROTATE_SPD = 18
    DAMAGE     = 16
    SIZE       = (70, 70)
    MAX_DIST   = 420    # disparaît après ~420 px parcourus (un tiers d'écran)

    def __init__(self, x, y, direction, owner):
        super().__init__(x, y, direction, owner)
        self.rotation      = 0.0
        self._dist_traveled = 0.0

        path = os.path.join("assets", "Perso", "samourai", "projo", "projo_shuriken_1.png")
        try:
            img = pygame.image.load(path).convert_alpha()
            self._sprite_base = pygame.transform.scale(img, self.SIZE)
        except Exception:
            surf = pygame.Surface(self.SIZE, pygame.SRCALPHA)
            for angle in range(0, 360, 90):
                rad = math.radians(angle)
                cx, cy = self.SIZE[0]//2, self.SIZE[1]//2
                ex = int(cx + math.cos(rad) * cx * 0.9)
                ey = int(cy + math.sin(rad) * cy * 0.9)
                pygame.draw.line(surf, (180, 180, 200), (cx, cy), (ex, ey), 5)
            pygame.draw.circle(surf, (120, 120, 160), (self.SIZE[0]//2, self.SIZE[1]//2), 8)
            self._sprite_base = surf

    def tick(self):
        self.x              += self.direction * self.SPEED
        self._dist_traveled += self.SPEED
        self.rotation        = (self.rotation + self.ROTATE_SPD * self.direction) % 360
        if self._out_of_screen() or self._dist_traveled >= self.MAX_DIST:
            self.active = False

    def render(self, render_engine):
        if not self.active:
            return
        rotated = pygame.transform.rotate(self._sprite_base, self.rotation)
        cx = int(self.x) + self.width  // 2
        cy = int(self.y) + self.height // 2
        render_engine.internal_surface.blit(rotated, (cx - rotated.get_width() // 2,
                                                       cy - rotated.get_height() // 2))


# -----------------------------------------------------------------------
# Robot — explosion au sol (attack2)
# -----------------------------------------------------------------------

class ExplosionEffect(_BaseProjectile):
    """
    Animation d'explosion sur place au sol devant le Robot.
    Ne se déplace pas — joue les 4 frames puis disparaît.
    La hitbox est gérée côté Player (attack2_hitbox), pas ici.
    """
    DAMAGE         = 0     # les dégâts sont gérés par attack2_hitbox du Player
    SIZE           = (180, 180)
    FRAMES_PER_IMG = 4     # chaque image dure 4 frames (16 frames total = ~0.53s à 30Hz)
    FRAME_ORDER    = [1, 2, 3, 4]  # explosion_1 → explosion_2 → explosion_3 → explosion_4

    def __init__(self, x, y, direction, owner):
        super().__init__(x, y, direction, owner)
        self._sprites    = []
        self._anim_frame = 0
        self._total_frames = len(self.FRAME_ORDER) * self.FRAMES_PER_IMG

        for idx in self.FRAME_ORDER:
            path = os.path.join("assets", "Perso", "robot", "projo", f"explosion_{idx}.png")
            try:
                img = pygame.image.load(path).convert_alpha()
                self._sprites.append(pygame.transform.scale(img, self.SIZE))
            except Exception:
                surf = pygame.Surface(self.SIZE, pygame.SRCALPHA)
                r = int(200 * (1 - idx / len(self.FRAME_ORDER)))
                pygame.draw.circle(surf, (r, 100, 255, 180),
                                   (self.SIZE[0]//2, self.SIZE[1]//2),
                                   self.SIZE[0]//2 - 10)
                self._sprites.append(surf)

    def tick(self):
        self._anim_frame += 1
        if self._anim_frame >= self._total_frames:
            self.active = False

    def render(self, render_engine):
        if not self.active or not self._sprites:
            return
        frame_idx = min(self._anim_frame // self.FRAMES_PER_IMG, len(self._sprites) - 1)
        img = self._sprites[frame_idx]
        # Centré horizontalement sur la position, bas de l'explosion au sol
        cx = int(self.x) + self.width  // 2
        cy = int(self.y) + self.height // 2
        render_engine.internal_surface.blit(img, (cx - img.get_width()  // 2,
                                                   cy - img.get_height() // 2))


# -----------------------------------------------------------------------
# Alias rétro-compatible
# -----------------------------------------------------------------------
Projectile = RobotProjectile