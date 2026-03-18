import pygame
import os


class Projectile:
    """
    Boule tirée par le Robot.
    - Se déplace horizontalement jusqu'à sortir de l'écran ou toucher l'adversaire.
    - Animée entre projo_1.png et projo_2.png.
    - Porte les informations de dégâts et d'appartenance (owner).
    """

    SPEED = 14          # px/frame (un peu plus vite que le robot)
    DAMAGE = 18
    ANIM_INTERVAL = 6   # change de sprite toutes les 6 frames

    # Taille d'affichage de la boule
    SIZE = (60,60)

    def __init__(self, x, y, direction, owner):
        """
        x, y       : position de départ (centre du sprite du robot)
        direction  : +1 vers la droite, -1 vers la gauche
        owner      : référence au joueur qui a tiré (pour éviter de se blesser soi-même)
        """
        self.x = x
        self.y = y
        self.direction = direction
        self.owner = owner
        self.active = True   # False quand elle doit être supprimée

        # --- Chargement des sprites ---
        self.sprites = []
        for i in range(1, 3):  # projo_1.png et projo_2.png
            path = os.path.join("assets", "Perso", "robot", "projo", f"projo_{i}.png")
            try:
                img = pygame.image.load(path).convert_alpha()
                img = pygame.transform.scale(img, self.SIZE)
                self.sprites.append(img)
            except Exception as e:
                print(f"Erreur chargement projectile {path}: {e}")
                # Fallback : surface colorée
                surf = pygame.Surface(self.SIZE, pygame.SRCALPHA)
                surf.fill((255, 100, 0))
                self.sprites.append(surf)

        self.anim_timer = 0
        self.width = self.SIZE[0]
        self.height = self.SIZE[1]

    @property
    def hitbox(self):
        margin = 15
        return pygame.Rect(
            self.x + margin,
            self.y + margin,
            self.width - margin * 2,
            self.height - margin * 2
        )
    
    def tick(self):
        """Déplace la boule et vérifie si elle sort de l'écran"""
        self.x += self.direction * self.SPEED

        # Animation
        self.anim_timer += 1
        if self.anim_timer >= self.ANIM_INTERVAL * len(self.sprites):
            self.anim_timer = 0

        # Sortie d'écran → suppression
        if self.x < -self.width or self.x > 1280:
            self.active = False

    def render(self, render_engine):
        if not self.active:
            return

        frame_idx = (self.anim_timer // self.ANIM_INTERVAL) % len(self.sprites)
        img = self.sprites[frame_idx]

        # Flip si elle va vers la gauche
        if self.direction < 0:
            img = pygame.transform.flip(img, True, False)

        render_engine.internal_surface.blit(img, (int(self.x), int(self.y)))
