import pygame

class GameUI:
    def __init__(self, width, height, match_duration=180):
        self.width = width
        self.height = height
        self.match_duration = match_duration
        self.time_remaining = match_duration
        self.match_started = False
        self.start_time = 0

        # Joueurs (enregistrés via set_players)
        self.p1 = None
        self.p2 = None
        self.show_controls = False
        self.game_over = False
        self.winner = None

        # Paramètres des barres de vie
        self.health_bar_width = 400
        self.health_bar_height = 30
        self.health_bar_y = 20

        # Fonts
        self.font_big = pygame.font.SysFont("Arial", 60, bold=True)
        self.font_medium = pygame.font.SysFont("Arial", 30, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 20, bold=True)

    def set_players(self, p1, p2=None, show_controls=False):
        """Enregistre les références des joueurs — à appeler avant le match"""
        self.p1 = p1
        self.p2 = p2
        self.show_controls = show_controls

    def set_game_over(self, winner):
        """Signale la fin du match avec le nom du gagnant (ou None pour égalité)"""
        self.game_over = True
        self.winner = winner

    def start_match(self):
        """Démarre le chronomètre"""
        self.match_started = True
        self.start_time = pygame.time.get_ticks()
        self.game_over = False
        self.winner = None

    def reset_timer(self):
        """Réinitialise le timer"""
        self.time_remaining = self.match_duration
        self.match_started = False
        self.game_over = False
        self.winner = None

    def update(self):
        """Met à jour le timer — à appeler depuis EngineTick"""
        if self.match_started:
            elapsed = (pygame.time.get_ticks() - self.start_time) / 1000
            self.time_remaining = max(0, self.match_duration - elapsed)

    def is_time_up(self):
        """Vérifie si le temps est écoulé"""
        return self.time_remaining <= 0

    def format_time(self, seconds):
        """Formate le temps en MM:SS"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"

    def draw_health_bar(self, surface, x, y, health, max_health, player_name, color, flip=False):
        """Dessine une barre de vie. flip=True : se remplit de droite à gauche"""
        border_color = (50, 50, 50)
        pygame.draw.rect(surface, border_color,
                         (x - 2, y - 2, self.health_bar_width + 4, self.health_bar_height + 4),
                         border_radius=5)

        bg_color = (80, 20, 20)
        pygame.draw.rect(surface, bg_color,
                         (x, y, self.health_bar_width, self.health_bar_height),
                         border_radius=3)

        health_ratio = max(0, min(1, health / max_health))
        current_width = int(self.health_bar_width * health_ratio)

        if health_ratio > 0.6:
            bar_color = color
        elif health_ratio > 0.3:
            bar_color = (255, 200, 0)
        else:
            bar_color = (255, 50, 50)

        if current_width > 0:
            bar_x = x + (self.health_bar_width - current_width) if flip else x
            pygame.draw.rect(surface, bar_color,
                             (bar_x, y, current_width, self.health_bar_height),
                             border_radius=3)

        name_surf = self.font_small.render(player_name, True, (255, 255, 255))
        name_x = x if not flip else x + self.health_bar_width - name_surf.get_width()
        surface.blit(name_surf, (name_x, y - 25))

        health_text = f"{int(health)}/{int(max_health)}"
        health_surf = self.font_small.render(health_text, True, (255, 255, 255))
        health_rect = health_surf.get_rect(center=(x + self.health_bar_width // 2, y + self.health_bar_height // 2))
        shadow_surf = self.font_small.render(health_text, True, (0, 0, 0))
        surface.blit(shadow_surf, (health_rect.x + 2, health_rect.y + 2))
        surface.blit(health_surf, health_rect)

    def draw_timer(self, surface):
        """Dessine le timer au centre en haut"""
        time_str = self.format_time(self.time_remaining)

        if self.time_remaining > 30:
            color = (255, 255, 255)
        elif self.time_remaining > 10:
            color = (255, 200, 0)
        else:
            color = (255, 50, 50)

        timer_width = 200
        timer_height = 80
        timer_x = self.width // 2 - timer_width // 2
        timer_y = 10

        timer_bg = pygame.Surface((timer_width, timer_height))
        timer_bg.set_alpha(180)
        timer_bg.fill((30, 30, 30))
        surface.blit(timer_bg, (timer_x, timer_y))

        pygame.draw.rect(surface, color,
                         (timer_x, timer_y, timer_width, timer_height), 3, border_radius=10)

        time_surf = self.font_big.render(time_str, True, color)
        time_rect = time_surf.get_rect(center=(self.width // 2, timer_y + timer_height // 2))
        shadow_surf = self.font_big.render(time_str, True, (0, 0, 0))
        surface.blit(shadow_surf, (time_rect.x + 3, time_rect.y + 3))
        surface.blit(time_surf, time_rect)

    def draw_game_over(self, surface):
        """Affiche l'écran de fin de partie"""
        overlay = pygame.Surface((self.width, self.height))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))

        if self.winner:
            text = f"{self.winner} GAGNE !"
            color = (255, 215, 0)
        else:
            text = "ÉGALITÉ !"
            color = (200, 200, 200)

        game_over_surf = self.font_big.render(text, True, color)
        game_over_rect = game_over_surf.get_rect(center=(self.width // 2, self.height // 2 - 50))
        shadow_surf = self.font_big.render(text, True, (0, 0, 0))
        surface.blit(shadow_surf, (game_over_rect.x + 4, game_over_rect.y + 4))
        surface.blit(game_over_surf, game_over_rect)

        instruction = "Appuyez sur ÉCHAP pour revenir au menu"
        instr_surf = self.font_small.render(instruction, True, (200, 200, 200))
        instr_rect = instr_surf.get_rect(center=(self.width // 2, self.height // 2 + 50))
        surface.blit(instr_surf, instr_rect)

    def draw_controls(self, surface):
        """Affiche les contrôles des joueurs"""
        y_pos = self.height - 60

        p1_surf = self.font_small.render("P1: Q/D + ESPACE", True, (150, 255, 150))
        surface.blit(p1_surf, (50, y_pos))

        p2_surf = self.font_small.render("P2: ← / → + ↑", True, (255, 150, 150))
        surface.blit(p2_surf, (self.width - p2_surf.get_width() - 50, y_pos))

    def render(self, surface):
        """Dessine tous les éléments UI — appelé par EngineRender, pas par main"""
        if self.p1 is None:
            return

        self.draw_timer(surface)

        self.draw_health_bar(surface, 40, self.health_bar_y + 80,
                             self.p1.health, self.p1.max_health,
                             "JOUEUR 1", (100, 255, 100))

        if self.p2:
            p2_x = self.width - self.health_bar_width - 40
            self.draw_health_bar(surface, p2_x, self.health_bar_y + 80,
                                 self.p2.health, self.p2.max_health,
                                 "JOUEUR 2", (255, 100, 100), flip=True)

        if self.show_controls:
            self.draw_controls(surface)

        if self.game_over:
            self.draw_game_over(surface)