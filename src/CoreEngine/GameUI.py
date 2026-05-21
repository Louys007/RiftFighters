import pygame
import math

# Durée d'affichage du bandeau punition en millisecondes
PUNISH_BANNER_DURATION_MS = 1800


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
        self.font_big    = pygame.font.SysFont("Consolas", 60, bold=True)
        self.font_medium = pygame.font.SysFont("Consolas", 30, bold=True)
        self.font_small  = pygame.font.SysFont("Consolas", 20, bold=True)
        self.font_punish = pygame.font.SysFont("Consolas", 48, bold=True)

        # --- Bandeaux PUNITION ---
        # Chaque entrée : {"side": "left"|"right", "start_ms": int}
        self.punish_banners = []

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
        """Met à jour le timer — à appeler depuis la boucle principale"""
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

    # ------------------------------------------------------------------ #
    #  BARRES DE VIE
    # ------------------------------------------------------------------ #

    def draw_health_bar(self, surface, x, y, health, max_health, player_name, color, flip=False):
        """Dessine une barre de vie inclinée style E-Sport. flip=True : se remplit de droite à gauche"""
        slant = 30
        w = self.health_bar_width
        h = self.health_bar_height

        def get_poly(x_pos, w_val):
            if not flip:
                return [(x_pos, y+h), (x_pos+slant, y), (x_pos+w_val+slant, y), (x_pos+w_val, y+h)]
            else:
                return [(x_pos, y), (x_pos-slant, y+h), (x_pos+w_val-slant, y+h), (x_pos+w_val, y)]

        bg_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        bg_poly = get_poly(x, w)
        pygame.draw.polygon(bg_surf, (15, 10, 15, 200), bg_poly)
        surface.blit(bg_surf, (0, 0))
        pygame.draw.polygon(surface, (30, 40, 50), bg_poly, 2)

        health_ratio = max(0, min(1, health / max_health))
        current_width = int(w * health_ratio)

        if health_ratio > 0.6:
            bar_color = color
        elif health_ratio > 0.3:
            bar_color = (255, 200, 0)
        else:
            bar_color = (255, 50, 50)

        if current_width > 0:
            fill_x = x if not flip else x + w - current_width
            fill_poly = get_poly(fill_x, current_width)
            pygame.draw.polygon(surface, bar_color, fill_poly)
            pygame.draw.polygon(surface, (255, 255, 255), fill_poly, 1)

        name_surf = self.font_small.render(player_name, True, (255, 255, 255))
        name_x = x + slant if not flip else x + w - name_surf.get_width() - slant
        surface.blit(name_surf, (name_x, y - 25))

        health_text = f"{int(health)}/{int(max_health)}"
        health_surf = self.font_small.render(health_text, True, (255, 255, 255))
        cx = x + w//2 + (slant//2 if not flip else -slant//2)
        cy = y + h//2
        health_rect = health_surf.get_rect(center=(cx, cy))
        shadow_surf = self.font_small.render(health_text, True, (0, 0, 0))
        surface.blit(shadow_surf, (health_rect.x + 2, health_rect.y + 2))
        surface.blit(health_surf, health_rect)

    # ------------------------------------------------------------------ #
    #  TIMER
    # ------------------------------------------------------------------ #

    def draw_timer(self, surface):
        """Dessine le timer au centre en haut"""
        time_str = self.format_time(self.time_remaining)
        t = pygame.time.get_ticks()

        if self.time_remaining > 30:
            color = (0, 255, 255)
        elif self.time_remaining > 10:
            color = (255, 200, 0)
        else:
            if (t // 500) % 2 == 0:
                color = (255, 50, 50)
            else:
                color = (200, 0, 0)

        timer_width = 180
        timer_height = 70
        timer_x = self.width // 2 - timer_width // 2
        timer_y = 10

        timer_bg = pygame.Surface((timer_width, timer_height), pygame.SRCALPHA)
        pygame.draw.rect(timer_bg, (10, 20, 30, 200), (0, 0, timer_width, timer_height), border_radius=15)
        pygame.draw.rect(timer_bg, color, (0, 0, timer_width, timer_height), 2, border_radius=15)

        scan_y = (t * 0.05) % timer_height
        pygame.draw.line(timer_bg, color, (0, scan_y), (timer_width, scan_y), 1)

        surface.blit(timer_bg, (timer_x, timer_y))

        time_surf = self.font_big.render(time_str, True, color)
        time_rect = time_surf.get_rect(center=(self.width // 2, timer_y + timer_height // 2))
        shadow_surf = self.font_big.render(time_str, True, (0, 0, 0))
        surface.blit(shadow_surf, (time_rect.x + 3, time_rect.y + 3))
        surface.blit(time_surf, time_rect)

    # ------------------------------------------------------------------ #
    #  GAME OVER
    # ------------------------------------------------------------------ #

    def draw_game_over(self, surface):
        """Affiche l'écran de fin de partie"""
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, (0, 0))

        if self.winner:
            text = f"{self.winner} GAGNE !"
            base_col = (0, 255, 255)
        else:
            text = "ÉGALITÉ !"
            base_col = (200, 200, 200)

        t = pygame.time.get_ticks()
        glitch_offset = math.sin(t * 0.05) * 5 if self.winner else 0

        cy = self.height // 2 - 50
        cx = self.width // 2

        surf_r    = self.font_big.render(text, True, (255, 0, 0))
        surf_b    = self.font_big.render(text, True, (0, 0, 255))
        surf_main = self.font_big.render(text, True, base_col)

        rect_main = surf_main.get_rect(center=(cx, cy))

        surface.blit(surf_r,    (rect_main.x - glitch_offset, rect_main.y))
        surface.blit(surf_b,    (rect_main.x + glitch_offset, rect_main.y))
        surface.blit(surf_main, rect_main)

        instruction = "Appuyez sur ÉCHAP pour revenir au menu"
        instr_surf = self.font_medium.render(instruction, True, (200, 200, 200))
        instr_rect = instr_surf.get_rect(center=(cx, cy + 80))

        if (t // 500) % 2 == 0:
            surface.blit(instr_surf, instr_rect)

    # ------------------------------------------------------------------ #
    #  CONTRÔLES
    # ------------------------------------------------------------------ #

    def draw_controls(self, surface):
        """Affiche les contrôles des joueurs"""
        y_pos = self.height - 60

        p1_surf = self.font_small.render("P1: Q/D + ESPACE", True, (150, 255, 150))
        surface.blit(p1_surf, (50, y_pos))

        p2_surf = self.font_small.render("P2: ← / → + ↑", True, (255, 150, 150))
        surface.blit(p2_surf, (self.width - p2_surf.get_width() - 50, y_pos))

    # ------------------------------------------------------------------ #
    #  BANDEAUX PUNITION
    # ------------------------------------------------------------------ #

    def trigger_punish_banner(self, attacker_player):
        """
        Déclenche un bandeau PUNITION du côté de l'attaquant.
        attacker_player : référence au Player qui a puni.
        """
        if attacker_player is self.p1:
            side = "left"
        else:
            side = "right"
        self.punish_banners.append({
            "side": side,
            "start_ms": pygame.time.get_ticks()
        })

    def draw_punish_banners(self, surface):
        """
        Dessine les bandeaux PUNITION actifs.
        Animation : slide depuis le bord + fade-in / fade-out + pulsation du texte.
        Sous-texte "×2 DÉGÂTS" pour renforcer la lisibilité.
        """
        t = pygame.time.get_ticks()
        active = []

        for banner in self.punish_banners:
            elapsed  = t - banner["start_ms"]
            if elapsed > PUNISH_BANNER_DURATION_MS:
                continue
            active.append(banner)

            progress = elapsed / PUNISH_BANNER_DURATION_MS   # 0.0 → 1.0

            # --- Opacité : fade-in rapide, plein pendant le centre, fade-out en fin ---
            if progress < 0.10:
                alpha = int(255 * (progress / 0.10))
            elif progress > 0.72:
                alpha = int(255 * (1.0 - (progress - 0.72) / 0.28))
            else:
                alpha = 255

            # --- Slide cubic-ease depuis le bord de l'écran ---
            slide_t    = min(1.0, progress / 0.14)
            slide_ease = 1.0 - (1.0 - slide_t) ** 3

            banner_w = 340
            banner_h = 80
            banner_y = self.height // 2 - banner_h // 2 - 20

            if banner["side"] == "left":
                x_final = 30
                x_start = -banner_w - 20
                accent_color = (100, 255, 100)    # vert J1
            else:
                x_final = self.width - banner_w - 30
                x_start = self.width + 20
                accent_color = (255, 100, 100)    # rouge J2

            banner_x = int(x_start + (x_final - x_start) * slide_ease)

            # --- Construction du panneau ---
            panel = pygame.Surface((banner_w, banner_h), pygame.SRCALPHA)

            # Fond sombre
            pygame.draw.rect(panel, (8, 4, 0, min(alpha, 210)),
                             (0, 0, banner_w, banner_h), border_radius=10)

            # Bordure dorée
            pygame.draw.rect(panel, (255, 200, 0, alpha),
                             (0, 0, banner_w, banner_h), 3, border_radius=10)

            # Barre latérale colorée (couleur du joueur qui punit)
            bar_surf = pygame.Surface((8, banner_h), pygame.SRCALPHA)
            pygame.draw.rect(bar_surf, (*accent_color, alpha),
                             (0, 0, 8, banner_h), border_radius=4)
            panel.blit(bar_surf, (0, 0))

            # --- Texte "PUNITION !" avec pulsation dorée ---
            pulse     = (math.sin(elapsed * 0.018) + 1) / 2
            gold_g    = int(190 + 65 * pulse)
            text_surf = self.font_punish.render("PUNITION !", True, (255, gold_g, 0))
            text_surf.set_alpha(alpha)

            shadow_surf = self.font_punish.render("PUNITION !", True, (0, 0, 0))
            shadow_surf.set_alpha(min(alpha, 170))

            tx = banner_w // 2 - text_surf.get_width() // 2 + 6   # +6 pour laisser place à la barre
            ty = banner_h // 2 - text_surf.get_height() // 2 - 6

            panel.blit(shadow_surf, (tx + 2, ty + 2))
            panel.blit(text_surf,   (tx,     ty))

            # --- Sous-texte "×2 DÉGÂTS" ---
            sub_font = pygame.font.SysFont("Consolas", 15, bold=True)
            sub_surf = sub_font.render("×2 DÉGÂTS", True, (255, gold_g, 0))
            sub_surf.set_alpha(alpha)
            sx = banner_w // 2 - sub_surf.get_width() // 2 + 6
            sy = ty + text_surf.get_height() + 2
            panel.blit(sub_surf, (sx, sy))

            surface.blit(panel, (banner_x, banner_y))

        self.punish_banners = active

    # ------------------------------------------------------------------ #
    #  RENDU PRINCIPAL
    # ------------------------------------------------------------------ #

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

        # Bandeaux PUNITION (au-dessus de tout sauf le game over)
        self.draw_punish_banners(surface)

        if self.game_over:
            self.draw_game_over(surface)