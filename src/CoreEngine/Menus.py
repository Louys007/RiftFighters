import pygame
import os
import math
import random
import math
from src.CoreEngine.KeyBindings import key_name, get_all, set_key, reset_defaults, ACTIONS, ACTION_LABELS


def draw_glass_panel(surface, x, y, w, h, base_color=(10, 15, 30), neon_color=(0, 255, 255), alpha=180, corner_cut=15):
    bg = pygame.Surface((w, h), pygame.SRCALPHA)
    p_r = w - 2
    p_b = h - 2
    points = [
        (corner_cut, 1), (p_r, 1),
        (p_r, p_b - corner_cut), (p_r - corner_cut, p_b),
        (1, p_b), (1, corner_cut)
    ]
    pygame.draw.polygon(bg, (*base_color, alpha), points)
    pygame.draw.polygon(bg, neon_color, points, 2)
    
    # Glowing accents
    pygame.draw.line(bg, neon_color, (1, corner_cut), (corner_cut, 1), 4)
    pygame.draw.line(bg, neon_color, (p_r - corner_cut, p_b), (p_r, p_b - corner_cut), 4)
    
    surface.blit(bg, (x, y))

def draw_neon_bar(surface, x, y, w, h, value, max_value, color):
    ratio = min(1.0, max(0.0, value / max_value))
    bg_rect = pygame.Rect(x, y, w, h)
    pygame.draw.rect(surface, (20, 30, 50), bg_rect, border_radius=int(h/2))
    if ratio > 0:
        fill_w = int(w * ratio)
        fill_rect = pygame.Rect(x, y, fill_w, h)
        pygame.draw.rect(surface, color, fill_rect, border_radius=int(h/2))
        glow_col = (min(255, color[0]+50), min(255, color[1]+50), min(255, color[2]+50))
        pygame.draw.rect(surface, glow_col, (x+2, y+h//2-1, max(1, fill_w-4), 2))


def draw_text_centered(surface, text, y, size=40, color=(255, 255, 255), outline=True):
    font = pygame.font.SysFont("Consolas", size, bold=True)
    
    if outline:
        outline_color = (0, 0, 0)
        for dx, dy in [(-2, -2), (2, -2), (-2, 2), (2, 2), (-1, 0), (1, 0), (0, -1), (0, 1)]:
            txt_shadow = font.render(text, True, outline_color)
            r_shadow = txt_shadow.get_rect(center=(surface.get_width() // 2 + dx, y + dy))
            surface.blit(txt_shadow, r_shadow)

    txt_surf = font.render(text, True, color)
    rect = txt_surf.get_rect(center=(surface.get_width() // 2, y))
    surface.blit(txt_surf, rect)


class Button:
    def __init__(self, x, y, width, height, text, action_code, color=(30, 40, 60), hover_color=(50, 70, 120),
                 text_color=(255, 255, 255), image_path=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action_code = action_code
        self.base_color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.font = pygame.font.SysFont("Consolas", 22, bold=True)
        self.is_hovered = False
        self.image_path = image_path

        self.image = None
        if image_path and os.path.exists(image_path):
            try:
                img_raw = pygame.image.load(image_path).convert_alpha()
                self.image = pygame.transform.scale(img_raw, (width, height))
            except Exception as e:
                print(f"Erreur chargement image bouton {image_path}: {e}")

    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered:
                return self.action_code
        return None

    def draw(self, surface):
        anim_offset = 2 if self.is_hovered else 0
        shadow_rect = self.rect.copy()
        shadow_rect.y += 4
        
        t = pygame.time.get_ticks()
        
        if self.image:
            pygame.draw.rect(surface, (0, 0, 0), shadow_rect, border_radius=10)
            draw_rect = self.rect.copy()
            draw_rect.y -= anim_offset
            
            surface.blit(self.image, draw_rect)
            
            if self.is_hovered:
                pulse = (math.sin(t * 0.01) + 1) / 2
                border_col = (0, int(155 + 100 * pulse), int(155 + 100 * pulse))
                pygame.draw.rect(surface, border_col, draw_rect, 3, border_radius=10)
            else:
                pygame.draw.rect(surface, (80, 80, 80), draw_rect, 2, border_radius=10)
                
            text_surf = self.font.render(self.text, True, self.text_color)
            text_rect = text_surf.get_rect(center=draw_rect.center)
            
            bg_text = pygame.Surface((text_rect.width + 10, text_rect.height + 4), pygame.SRCALPHA)
            bg_text.fill((0, 0, 0, 180))
            surface.blit(bg_text, (text_rect.x - 5, text_rect.y - 2))
            
            surface.blit(text_surf, text_rect)
        else:
            pygame.draw.rect(surface, (10, 10, 15), shadow_rect, border_radius=10)
            
            draw_rect = self.rect.copy()
            draw_rect.y -= anim_offset
            
            color = self.hover_color if self.is_hovered else self.base_color
            border_col = (0, 255, 255) if self.is_hovered else (80, 100, 150)
            
            if self.is_hovered:
                pulse = (math.sin(t * 0.01) + 1) / 2
                border_col = (
                    int(border_col[0] * (0.5 + 0.5 * pulse)),
                    int(border_col[1] * (0.5 + 0.5 * pulse)),
                    int(border_col[2] * (0.5 + 0.5 * pulse))
                )
            
            pygame.draw.rect(surface, color, draw_rect, border_radius=10)
            pygame.draw.rect(surface, border_col, draw_rect, 2, border_radius=10)
            
            text_surf = self.font.render(self.text, True, self.text_color)
            text_rect = text_surf.get_rect(center=draw_rect.center)
            
            shadow_surf = self.font.render(self.text, True, (0, 0, 0))
            surface.blit(shadow_surf, (text_rect.x + 1, text_rect.y + 2))
            
            surface.blit(text_surf, text_rect)


class InputBox:
    def __init__(self, x, y, w, h, text=''):
        self.rect = pygame.Rect(x, y, w, h)
        self.color_inactive = pygame.Color('lightskyblue3')
        self.color_active = pygame.Color('dodgerblue2')
        self.color = self.color_inactive
        self.text = text
        self.font = pygame.font.Font(None, 32)
        self.txt_surface = self.font.render(text, True, self.color)
        self.active = False

    def handle_event(self, event, mouse_pos):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(mouse_pos):
                self.active = not self.active
            else:
                self.active = False
            self.color = self.color_active if self.active else self.color_inactive

        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    pass
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    if len(self.text) < 20:
                        self.text += event.unicode
                self.txt_surface = self.font.render(self.text, True, self.color)

    def draw(self, screen):
        screen.blit(self.txt_surface, (self.rect.x + 5, self.rect.y + 5))
        pygame.draw.rect(screen, self.color, self.rect, 2)


class MenuSystem:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.state = "MENU_MAIN"
        self.clock = pygame.time.Clock()

        self.popup_error = None
        self.btn_popup_ok = Button(width // 2 - 100, 350, 200, 50, "OK", "CLOSE_POPUP")

        self.selected_mode = None
        self.selected_ip = "localhost"
        self.selected_stage = "Lab.png"
        self.selected_solo_type = "1v0"
        self.selected_char_p1 = None
        self.selected_char_p2 = None

        # --- PERSONNAGES ---
        self.available_chars = [
            {
                "id": "Cromagnon",
                "name": "Cromagnon",
                "color": (0, 255, 0),
                "image": "cromagnon/cromagnon_idle.png",
                "stats": {"speed": 14, "jump": 28, "gravity": 2}
            },
            {
                "id": "Robot",
                "name": "Robot",
                "color": (255, 50, 50),
                "image": "robot/robot_idle.png",
                "stats": {"speed": 10, "jump": 35, "gravity": 2}
            },
            {
                "id": "Samourai",
                "name": "Samourai",
                "color": (150, 50, 255),
                "image": "samourai/samourai_idle.png",
                "stats": {"speed": 16, "jump": 32, "gravity": 2}
            }
        ]

        self.selected_char_id = self.available_chars[0]["id"]
        self.available_stages = ["Lab.png", "Cave.png", "Futur.png", "FarWest.png", "NeoFutur.png", "Wasteland.png"]

        # --- PREVIEW SYSTEM ---
        self.preview_cache = {}
        self.hovered_stage_idx = None
        self.hovered_char_idx  = None

        # --- BOUTONS ---
        cx = width // 2
        bw = 200
        bx = cx - bw // 2

        self.main_buttons = [
            Button(bx, 200, bw, 50, "Entraînement", "PRE_SOLO"),
            Button(bx, 270, bw, 50, "Multijoueur", "GO_MULTI_MENU"),
            Button(bx, 340, bw, 50, "Règles", "GO_RULES"),
            Button(bx, 410, bw, 50, "Touches", "GO_KEYBINDINGS", color=(40, 80, 120), hover_color=(60, 120, 180)),
            Button(bx, 500, bw, 50, "Quitter", "QUIT", color=(200, 50, 50), hover_color=(255, 50, 50))
        ]

        bw_solo = 300
        bx_solo = cx - bw_solo // 2
        self.btn_solo_back = Button(50, height - 100, 150, 50, "Retour", "BACK")
        self.solo_type_buttons = [
            Button(bx_solo, 200, bw_solo, 60, "1v0 - Solo", "SELECT_SOLO_1V0", color=(100, 150, 255)),
            Button(bx_solo, 280, bw_solo, 60, "1v1 - Local", "SELECT_SOLO_1V1", color=(150, 100, 255)),
            Button(bx_solo, 360, bw_solo, 60, "1vBot - IA", "SELECT_SOLO_1VBOT", color=(255, 120, 30)),
            self.btn_solo_back
        ]

        # --- SÉLECTION DIFFICULTÉ BOT ---
        self.selected_bot_difficulty = "NORMAL"
        self.selected_bot_character  = None
        self.btn_diff_back = Button(50, height - 100, 150, 50, "Retour", "BACK_TO_SOLO_TYPE")
        self.diff_buttons = [
            Button(bx_solo, 200, bw_solo, 65, "FACILE",  "SELECT_DIFF_EASY",
                   color=(30, 120, 30),  hover_color=(50, 180, 50)),
            Button(bx_solo, 285, bw_solo, 65, "NORMAL",  "SELECT_DIFF_NORMAL",
                   color=(180, 130, 0),  hover_color=(230, 170, 0)),
            Button(bx_solo, 370, bw_solo, 65, "DIFFICILE","SELECT_DIFF_HARD",
                   color=(160, 30, 30),  hover_color=(220, 50, 50)),
            self.btn_diff_back
        ]

        self.btn_multi_back = Button(50, height - 100, 150, 50, "Retour", "BACK")
        self.multi_buttons = [
            Button(bx, 200, bw, 50, "Héberger (Host)", "PRE_HOST"),
            Button(bx, 360, bw, 50, "Rejoindre IP", "PRE_JOIN"),
            self.btn_multi_back
        ]
        self.ip_box = InputBox(bx, 300, bw, 40, "localhost")

        # Boutons Stages
        self.stage_scroll_offset = 0
        self.stage_buttons = []
        self.stage_button_width = 280
        self.stage_button_height = 140
        self.stage_columns = 2
        self.stage_padding = 20
        self.stage_start_x = 100
        self.stage_start_y = 150

        for i, stage in enumerate(self.available_stages):
            img_path = os.path.join("assets", "Stages", stage)
            col = i % self.stage_columns
            row = i // self.stage_columns
            x = self.stage_start_x + col * (self.stage_button_width + self.stage_padding)
            y = self.stage_start_y + row * (self.stage_button_height + self.stage_padding)
            self.stage_buttons.append(
                Button(x, y, self.stage_button_width, self.stage_button_height, stage, f"SELECT_STAGE_{i}", image_path=img_path)
            )
        self.btn_stage_back = Button(50, height - 100, 150, 50, "Retour", "BACK_TO_PREV")

        bw_char = 300
        bx_char = cx - bw_char // 2
        self.char_buttons = []
        for i, char_data in enumerate(self.available_chars):
            self.char_buttons.append(
                Button(bx_char, 150 + i * 70, bw_char, 60, char_data["name"], f"SELECT_CHAR_{i}", color=char_data["color"])
            )
        self.btn_char_back = Button(50, height - 100, 150, 50, "Retour", "BACK_TO_STAGE")

        self.char_buttons_p2 = []
        for i, char_data in enumerate(self.available_chars):
            self.char_buttons_p2.append(
                Button(bx_char, 150 + i * 70, bw_char, 60, char_data["name"], f"SELECT_CHAR_P2_{i}", color=char_data["color"])
            )
        self.btn_char_p2_back = Button(50, height - 100, 150, 50, "Retour", "BACK_TO_CHAR_P1")

        self.char_buttons_bot = []
        for i, char_data in enumerate(self.available_chars):
            self.char_buttons_bot.append(
                Button(bx_char, 150 + i * 70, bw_char, 60, char_data["name"], f"SELECT_CHAR_BOT_{i}", color=char_data["color"])
            )
        self.btn_char_bot_back = Button(50, height - 100, 150, 50, "Retour", "BACK_TO_CHAR_P1_BOT")

        self.btn_back = Button(50, height - 100, 150, 50, "Retour", "BACK")

        # --- KEYBINDINGS ---
        self.btn_kb_back = Button(50, height - 100, 150, 50, "Retour", "BACK")
        self.btn_kb_reset = Button(width - 230, height - 100, 200, 50, "Réinitialiser", "KB_RESET",
                                   color=(150, 60, 0), hover_color=(200, 90, 0))
        # Quel slot est en cours d'écoute : ("p1"/"p2", action) ou None
        self._kb_listening = None
        # Page affichée : "p1" ou "p2"
        self._kb_page = "p1"
        self._kb_page_buttons = [
            Button(cx - 220, 110, 200, 44, "JOUEUR 1", "KB_PAGE_P1", color=(30, 80, 30), hover_color=(50, 130, 50)),
            Button(cx + 20,  110, 200, 44, "JOUEUR 2", "KB_PAGE_P2", color=(80, 30, 30), hover_color=(130, 50, 50)),
        ]

    # ------------------------------------------------------------------ #
    #  PREVIEW
    # ------------------------------------------------------------------ #

    def load_preview_image(self, path, target_size):
        if path not in self.preview_cache:
            try:
                img = pygame.image.load(path).convert_alpha()
                img = pygame.transform.scale(img, target_size)
                self.preview_cache[path] = img
            except Exception:
                self.preview_cache[path] = None
        return self.preview_cache[path]

    def draw_stage_preview(self, surface, stage_idx):
        if stage_idx is None:
            return

        stage_name = self.available_stages[stage_idx]
        img_path = os.path.join("assets", "Stages", stage_name)

        preview_x = 750
        preview_y = 150
        preview_w = 450
        preview_h = 300

        draw_glass_panel(surface, preview_x - 20, preview_y - 60, preview_w + 40, preview_h + 120, neon_color=(0, 255, 255))

        font = pygame.font.SysFont("Consolas", 22, bold=True)
        title_surf = font.render("APERÇU DU STAGE", True, (0, 255, 255))
        surface.blit(title_surf, (preview_x + preview_w // 2 - title_surf.get_width() // 2, preview_y - 45))

        preview_img = self.load_preview_image(img_path, (preview_w, preview_h))
        if preview_img:
            t = pygame.time.get_ticks()
            surface.blit(preview_img, (preview_x, preview_y))
            # Scanlines overlay
            scanline_surf = pygame.Surface((preview_w, preview_h), pygame.SRCALPHA)
            for y_line in range(0, preview_h, 4):
                pygame.draw.line(scanline_surf, (0, 255, 255, 15), (0, y_line), (preview_w, y_line))
                
            scan_y = (t * 0.1) % preview_h
            pygame.draw.rect(scanline_surf, (0, 255, 255, 50), (0, scan_y, preview_w, 20))
            pygame.draw.line(scanline_surf, (0, 255, 255, 200), (0, scan_y+10), (preview_w, scan_y+10), 2)
            
            surface.blit(scanline_surf, (preview_x, preview_y))
            
            cx = preview_x + preview_w // 2
            cy = preview_y + preview_h // 2
            for _angle, radius, thickness in [(t * 0.05, 100, 2), (-t * 0.03, 120, 1)]:
                pts = []
                for i in range(3):
                    a = math.radians(_angle + i * 120)
                    pts.append((cx + math.cos(a)*radius, cy + math.sin(a)*radius))
                pygame.draw.polygon(surface, (0, 255, 255, 100), pts, thickness)
                
            pygame.draw.rect(surface, (0, 150, 255), (preview_x, preview_y, preview_w, preview_h), 2)
        else:
            pygame.draw.rect(surface, (30, 30, 30), (preview_x, preview_y, preview_w, preview_h))
            no_img_text = font.render("DISPONIBLE SUR RÉSEAU", True, (150, 150, 150))
            surface.blit(no_img_text, (preview_x + preview_w // 2 - no_img_text.get_width() // 2, preview_y + preview_h // 2))

        name_surf = pygame.font.SysFont("Consolas", 28, bold=True).render(stage_name.replace(".png", ""), True, (255, 255, 255))
        surface.blit(name_surf, (preview_x + preview_w // 2 - name_surf.get_width() // 2, preview_y + preview_h + 15))

    def draw_character_preview(self, surface, char_idx, side="left"):
        if char_idx is None:
            return

        char_data = self.available_chars[char_idx]
        preview_w = 350
        preview_h = 420
        t = pygame.time.get_ticks()

        if side == "left":
            preview_x = 50
            player_label = "JOUEUR 1"
            player_color = (0, 255, 150)
        else:
            preview_x = self.width - preview_w - 50
            player_label = "JOUEUR 2"
            player_color = (255, 50, 100)

        preview_y = 150

        draw_glass_panel(surface, preview_x - 10, preview_y - 65, preview_w + 20, preview_h + 100, neon_color=char_data["color"], alpha=150)

        font_small = pygame.font.SysFont("Consolas", 16, bold=True)
        player_surf = font_small.render(player_label, True, player_color)
        surface.blit(player_surf, (preview_x + preview_w // 2 - player_surf.get_width() // 2, preview_y - 50))

        name_font = pygame.font.SysFont("Consolas", 32, bold=True)
        name_surf = name_font.render(char_data["name"].upper(), True, (255, 255, 255))
        surface.blit(name_surf, (preview_x + preview_w // 2 - name_surf.get_width() // 2, preview_y - 15))

        cube_size = 140
        cube_x = preview_x + preview_w // 2 - cube_size // 2
        cube_y = preview_y + 60
        center_x, center_y = cube_x + cube_size//2, cube_y + cube_size//2

        # Anneau technologique rotatif
        angle = t * 0.05
        ring_radius = 85
        points = []
        for i in range(3):
            a = math.radians(angle + i * 120)
            points.append((center_x + math.cos(a)*ring_radius, center_y + math.sin(a)*ring_radius))
        pygame.draw.polygon(surface, char_data["color"], points, 2)
        pygame.draw.circle(surface, (char_data["color"][0], char_data["color"][1], char_data["color"][2], 100), (center_x, center_y), ring_radius, 1)

        img_path = os.path.join("assets", "Perso", char_data["image"])
        preview_img = self.load_preview_image(img_path, (cube_size, cube_size))

        if preview_img:
            bounce = math.sin(t * 0.005) * 5
            surface.blit(preview_img, (cube_x, cube_y + bounce))
        else:
            pygame.draw.rect(surface, char_data["color"], (cube_x, cube_y, cube_size, cube_size), border_radius=15)

        stats_y = cube_y + cube_size + 40
        stats_font = pygame.font.SysFont("Consolas", 16, bold=True)
        stats_list = [
            ("VITESSE", char_data['stats']['speed'], 20),
            ("PUISS. SAUT", abs(char_data['stats']['jump']), 40),
            ("GRAVITÉ", char_data['stats']['gravity'], 5)
        ]
        
        for i, (label, val, max_val) in enumerate(stats_list):
            stat_surf = stats_font.render(label, True, (180, 200, 220))
            surface.blit(stat_surf, (preview_x + 30, stats_y + i * 40))
            draw_neon_bar(surface, preview_x + 130, stats_y + i * 40 + 5, 180, 12, val, max_val, char_data["color"])

    # ------------------------------------------------------------------ #
    #  CONFIGURATION DES TOUCHES
    # ------------------------------------------------------------------ #

    def draw_keybindings_screen(self, surface):
        """
        Écran de remapping des touches.
        Affiche les 6 actions pour le joueur sélectionné.
        Cliquer sur une ligne → attend une touche → l'enregistre.
        """
        import pygame
        t = pygame.time.get_ticks()
        bindings = get_all()
        player   = self._kb_page
        cx       = self.width // 2

        draw_text_centered(surface, "CONFIGURATION DES TOUCHES", 65, size=38, color=(0, 255, 255))

        # Onglets P1 / P2
        for btn in self._kb_page_buttons:
            is_active = (btn.action_code == f"KB_PAGE_{player.upper()}")
            color = (20, 100, 20) if (is_active and player == "p1") else \
                    (100, 20, 20) if (is_active and player == "p2") else \
                    btn.base_color
            pygame.draw.rect(surface, color, btn.rect, border_radius=8)
            if is_active:
                pygame.draw.rect(surface, (0, 255, 200), btn.rect, 2, border_radius=8)
            else:
                pygame.draw.rect(surface, (80, 80, 80), btn.rect, 1, border_radius=8)
            lbl = pygame.font.SysFont("Consolas", 20, bold=True).render(btn.text, True, (255, 255, 255))
            surface.blit(lbl, lbl.get_rect(center=btn.rect.center))

        # Indication joueur actif
        player_label = "JOUEUR 1" if player == "p1" else "JOUEUR 2"
        player_color = (100, 255, 100) if player == "p1" else (255, 100, 100)
        draw_text_centered(surface, f"── {player_label} ──", 168, size=22, color=player_color)

        # Panneau des lignes
        panel_x = cx - 300
        panel_w = 600
        row_h   = 60
        rows_y  = 200

        draw_glass_panel(surface, panel_x - 10, rows_y - 10,
                         panel_w + 20, len(ACTIONS) * row_h + 20,
                         neon_color=player_color, alpha=120)

        font_label = pygame.font.SysFont("Consolas", 20, bold=True)
        font_key   = pygame.font.SysFont("Consolas", 22, bold=True)

        for i, action in enumerate(ACTIONS):
            row_y = rows_y + i * row_h
            is_listening = (self._kb_listening == (player, action))
            is_hovered   = pygame.Rect(panel_x, row_y, panel_w, row_h - 4).collidepoint(
                               pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1]
                           ) and not self._kb_listening

            # Fond de la ligne
            if is_listening:
                pulse = (math.sin(t * 0.015) + 1) / 2
                bg_color = (int(40 + 30 * pulse), int(20 + 20 * pulse), 0)
            elif is_hovered:
                bg_color = (30, 40, 60)
            else:
                bg_color = (15, 20, 30)

            row_surf = pygame.Surface((panel_w, row_h - 4), pygame.SRCALPHA)
            row_surf.fill((*bg_color, 200))
            surface.blit(row_surf, (panel_x, row_y))

            if is_listening or is_hovered:
                pygame.draw.rect(surface, player_color if not is_listening else (255, 200, 0),
                                 (panel_x, row_y, panel_w, row_h - 4), 2, border_radius=4)

            # Label de l'action
            lbl_surf = font_label.render(ACTION_LABELS.get(action, action), True,
                                         (255, 200, 0) if is_listening else (180, 200, 220))
            surface.blit(lbl_surf, (panel_x + 20, row_y + (row_h - 4) // 2 - lbl_surf.get_height() // 2))

            # Touche actuelle ou message d'attente
            if is_listening:
                pulse_a = int(180 + 75 * (math.sin(t * 0.02) + 1) / 2)
                key_surf = font_key.render("► APPUYEZ SUR UNE TOUCHE...", True, (255, 220, 0))
                key_surf.set_alpha(pulse_a)
            else:
                current_key = bindings[player][action]
                key_surf = font_key.render(key_name(current_key), True, player_color)

            surface.blit(key_surf, (panel_x + panel_w - key_surf.get_width() - 20,
                                    row_y + (row_h - 4) // 2 - key_surf.get_height() // 2))

        # Instructions bas de page
        hint_font = pygame.font.SysFont("Consolas", 16)
        hints = [
            "Cliquez sur une ligne pour modifier la touche",
            "ÉCHAP annule la saisie en cours",
        ]
        for j, hint in enumerate(hints):
            hs = hint_font.render(hint, True, (120, 130, 150))
            surface.blit(hs, (cx - hs.get_width() // 2, self.height - 145 + j * 22))

    # ------------------------------------------------------------------ #
    #  RÈGLES
    # ------------------------------------------------------------------ #

    def draw_rules(self, surface):
        draw_glass_panel(surface, 50, 40, self.width - 100, self.height - 80, neon_color=(0, 200, 255), alpha=200)

        draw_text_centered(surface, "BASE DE DONNÉES : CONTRÔLES & RÈGLES", 70, size=35, color=(0, 255, 255))
        pygame.draw.line(surface, (0, 150, 200), (300, 120), (self.width - 300, 120), 2)

        font_title = pygame.font.SysFont("Consolas", 22, bold=True)
        font_line  = pygame.font.SysFont("Consolas", 18)
        font_small = pygame.font.SysFont("Consolas", 15)

        cx = self.width // 2

        general = [
            "> SYSTÈME DE VICTOIRE : RÉDUISEZ LA VIE ADVERSE À 0",
            "> TIMEOUT : LE JOUEUR AVEC LE PLUS DE PV L'EMPORTE",
            "> CONNEXION MULTIJOUEUR : L'HÔTE INITIE LE MATCH"
        ]
        y_gen = 140
        for i, line in enumerate(general):
            surf = font_small.render(line, True, (150, 200, 200))
            surface.blit(surf, (cx - surf.get_width() // 2, y_gen + i * 22))

        col_x_left = 100
        y = 230
        
        draw_glass_panel(surface, col_x_left - 20, y - 20, cx - 120, 210, base_color=(10, 30, 20), neon_color=(0, 255, 150), corner_cut=10, alpha=100)
        p1_title = font_title.render("UNITÉ 1 : CLAVIER LOCAL", True, (100, 255, 100))
        surface.blit(p1_title, (col_x_left, y))
        y += 35

        common_p1 = [
            ("MOUVEMENT",  "Q  /  D",  (200, 255, 200)),
            ("SAUT",    "ESPACE",   (200, 255, 200)),
            ("ATTAQUE ARMÉE",  "G",        (255, 150,  50)),
            ("BOUCLIER ÉNERG.",  "N",        (50, 200, 255)),
            ("PROPULSION",      "2x ← ou →",(255, 200,  50)),
        ]
        for label, key, color in common_p1:
            surface.blit(font_line.render(f"[{label}]", True, (120, 180, 180)), (col_x_left, y))
            surface.blit(font_title.render(key, True, color), (col_x_left + 150, y-2))
            y += 30

        col_x_right = cx + 60
        y = 230
        
        draw_glass_panel(surface, col_x_right - 20, y - 20, cx - 120, 210, base_color=(30, 10, 10), neon_color=(255, 50, 50), corner_cut=10, alpha=100)
        p2_title = font_title.render("UNITÉ 2 : LOCAL / RÉSEAU", True, (255, 100, 100))
        surface.blit(p2_title, (col_x_right, y))
        y += 35

        common_p2 = [
            ("MOUVEMENT",  "← / →",    (255, 200, 200)),
            ("SAUT",    "↑",         (255, 200, 200)),
            ("ATTAQUE ARMÉE",  "ENTRÉE",    (255, 150,  50)),
            ("BOUCLIER ÉNERG.",  "M",         (50, 200, 255)),
            ("PROPULSION",      "2x ← ou →", (255, 200,  50)),
        ]
        for label, key, color in common_p2:
            surface.blit(font_line.render(f"[{label}]", True, (180, 120, 120)), (col_x_right, y))
            surface.blit(font_title.render(key, True, color), (col_x_right + 150, y-2))
            y += 30

        draw_glass_panel(surface, 100, 480, self.width - 200, 150, neon_color=(200, 150, 255), corner_cut=15, alpha=120)
        draw_text_centered(surface, "SYSTÈMES AVANCÉS", 500, size=20, color=(220, 180, 255))
        
        adv_font = pygame.font.SysFont("Consolas", 16)
        rules_text = [
            "[BOUCLIER] Bloque 80% des dégâts. Surcharge : 30 frames de stun après relâchement.",
            "[DASH] Double-tap directionnel. Traverse les ennemis. Désactivé pendant une attaque.",
            "[CROMAGNON] Puissance équilibrée. Frappe consistante à la lance.",
            "[ROBOT] Projectile d'énergie, contrôle à distance maximal.",
            "[SAMOURAÏ] Katana tranchant : combo rapide à haute dangerosité."
        ]
        
        y_adv = 540
        for r_line in rules_text:
            text_s = adv_font.render(r_line, True, (200, 200, 250))
            surface.blit(text_s, (130, y_adv))
            y_adv += 20

    # ------------------------------------------------------------------ #
    #  UTILITAIRES
    # ------------------------------------------------------------------ #

    def show_error(self, message):
        self.popup_error = message
        self.state = "MENU_MAIN"

    def _get_char_idx_by_id(self, char_id):
        for i, c in enumerate(self.available_chars):
            if c["id"] == char_id:
                return i
        return None

    # ------------------------------------------------------------------ #
    #  BOUCLE PRINCIPALE
    # ------------------------------------------------------------------ #

    def draw_background(self, surface):
        t = pygame.time.get_ticks()
        surface.fill((8, 10, 18))
        
        if not hasattr(self, 'particles'):
            self.particles = []
            for _ in range(50):
                self.particles.append([random.randint(0, self.width), random.randint(0, self.height), random.uniform(0.5, 2.0), random.uniform(1, 3)])
        
        for p in self.particles:
            p[1] -= p[2]
            if p[1] < 0:
                p[1] = self.height
                p[0] = random.randint(0, self.width)
            
            glow = (math.sin(t * 0.003 + p[0]) + 1) / 2
            color = (0, int(150 + 100 * glow), int(150 + 100 * glow))
            pygame.draw.circle(surface, color, (int(p[0]), int(p[1])), int(p[3]))
            pygame.draw.circle(surface, (*color, 50), (int(p[0]), int(p[1])), int(p[3]*3), 1)

        horizon_y = self.height // 2 + 100
        pygame.draw.rect(surface, (0, 0, 0, 180), (0, horizon_y, self.width, self.height - horizon_y))
        
        num_lines = 30
        center_x = self.width // 2
        for i in range(num_lines):
            progress = i / (num_lines - 1)
            x_top = center_x + (progress - 0.5) * self.width * 0.8
            x_bot = center_x + (progress - 0.5) * self.width * 3
            pygame.draw.line(surface, (0, 50, 100), (x_top, horizon_y), (x_bot, self.height), 2)
            
        speed = 0.001
        for i in range(15):
            phase = (i / 15 + t * speed) % 1.0
            y_line = horizon_y + phase**3 * (self.height - horizon_y)
            color_intensity = int(255 * phase**2)
            pygame.draw.line(surface, (0, min(150, color_intensity), min(255, color_intensity)), (0, y_line), (self.width, y_line), max(1, int(phase*4)))
            
        pygame.draw.line(surface, (0, 255, 255), (0, horizon_y), (self.width, horizon_y), 3)

        if not hasattr(self, 'bg_shadow'):
            self.bg_shadow = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            pygame.draw.rect(self.bg_shadow, (0, 0, 0, 150), (0, 0, self.width, 120))
            pygame.draw.rect(self.bg_shadow, (0, 0, 0, 150), (0, self.height - 120, self.width, 120))
        surface.blit(self.bg_shadow, (0, 0))

    def run(self, render_engine):
        running = True
        surface_to_draw = render_engine.internal_surface

        while running:
            self.draw_background(surface_to_draw)
            mouse_pos = render_engine.get_virtual_mouse_pos()

            self.hovered_stage_idx = None
            self.hovered_char_idx  = None

            active_buttons = []
            if self.popup_error:
                active_buttons = [self.btn_popup_ok]
            else:
                if self.state == "MENU_MAIN":
                    active_buttons = self.main_buttons
                elif self.state == "MENU_MULTI":
                    active_buttons = self.multi_buttons
                elif self.state == "RULES":
                    active_buttons = [self.btn_back]
                elif self.state == "MENU_SOLO_TYPE":
                    active_buttons = self.solo_type_buttons
                elif self.state == "MENU_STAGE":
                    active_buttons = self.stage_buttons + [self.btn_stage_back]
                elif self.state == "MENU_CHAR_P1":
                    active_buttons = self.char_buttons + [self.btn_char_back]
                elif self.state == "MENU_CHAR_P2":
                    active_buttons = self.char_buttons_p2 + [self.btn_char_p2_back]
                elif self.state == "MENU_CHAR":
                    active_buttons = self.char_buttons + [self.btn_char_back]
                elif self.state == "MENU_CHAR_BOT":
                    active_buttons = self.char_buttons_bot + [self.btn_char_bot_back]
                elif self.state == "MENU_DIFF_BOT":
                    active_buttons = self.diff_buttons
                elif self.state == "MENU_KEYBINDINGS":
                    active_buttons = [self.btn_kb_back, self.btn_kb_reset] + self._kb_page_buttons

            for btn in active_buttons:
                btn.check_hover(mouse_pos)

            if self.state == "MENU_STAGE":
                for i, btn in enumerate(self.stage_buttons):
                    adjusted_rect = pygame.Rect(btn.rect.x, btn.rect.y + self.stage_scroll_offset, btn.rect.width, btn.rect.height)
                    if adjusted_rect.collidepoint(mouse_pos):
                        btn.is_hovered = True
                        self.hovered_stage_idx = i
                        break
                    else:
                        btn.is_hovered = False
            elif self.state in ("MENU_CHAR_P1", "MENU_CHAR", "MENU_CHAR_P2", "MENU_CHAR_BOT"):
                btns = self.char_buttons_bot if self.state == "MENU_CHAR_BOT" else \
                       self.char_buttons_p2  if self.state == "MENU_CHAR_P2"  else \
                       self.char_buttons
                for i, btn in enumerate(btns):
                    if btn.is_hovered:
                        self.hovered_char_idx = i
                        break

            action = None
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return {'action': 'QUIT'}
                if event.type == pygame.VIDEORESIZE:
                    render_engine.update_scale_factors()

                # --- Gestion spéciale MENU_KEYBINDINGS ---
                if self.state == "MENU_KEYBINDINGS":
                    if self._kb_listening:
                        if event.type == pygame.KEYDOWN:
                            if event.key == pygame.K_ESCAPE:
                                self._kb_listening = None  # annule
                            else:
                                player, act = self._kb_listening
                                set_key(player, act, event.key)
                                self._kb_listening = None
                        # On ne passe pas les events aux boutons pendant l'écoute
                        continue

                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        # Vérifie si un clic tombe sur une ligne de l'écran
                        bindings = get_all()
                        panel_x  = self.width // 2 - 300
                        panel_w  = 600
                        row_h    = 60
                        rows_y   = 200
                        vx, vy   = render_engine.get_virtual_mouse_pos()
                        for i, act in enumerate(ACTIONS):
                            row_rect = pygame.Rect(panel_x, rows_y + i * row_h, panel_w, row_h - 4)
                            if row_rect.collidepoint(vx, vy):
                                self._kb_listening = (self._kb_page, act)
                                break
                if self.state == "MENU_STAGE" and event.type == pygame.MOUSEWHEEL:
                    num_rows = (len(self.available_stages) + self.stage_columns - 1) // self.stage_columns
                    total_height = num_rows * (self.stage_button_height + self.stage_padding)
                    visible_height = self.height - self.stage_start_y - 120
                    if total_height > visible_height:
                        self.stage_scroll_offset += event.y * 30
                        self.stage_scroll_offset = max(-(total_height - visible_height), min(0, self.stage_scroll_offset))
                if self.state == "MENU_MULTI" and not self.popup_error:
                    self.ip_box.handle_event(event, mouse_pos)
                for btn in active_buttons:
                    res = btn.handle_event(event)
                    if res:
                        action = res

            if action:
                if action == "CLOSE_POPUP":
                    self.popup_error = None
                elif not self.popup_error:
                    if action == "QUIT":
                        return {'action': 'QUIT'}
                    elif action == "BACK":
                        self._kb_listening = None
                        self.state = "MENU_MAIN"
                    elif action == "GO_MULTI_MENU":
                        self.state = "MENU_MULTI"
                    elif action == "GO_RULES":
                        self.state = "RULES"
                    elif action == "GO_KEYBINDINGS":
                        self._kb_listening = None
                        self._kb_page = "p1"
                        self.state = "MENU_KEYBINDINGS"
                    elif action == "KB_PAGE_P1":
                        self._kb_listening = None
                        self._kb_page = "p1"
                    elif action == "KB_PAGE_P2":
                        self._kb_listening = None
                        self._kb_page = "p2"
                    elif action == "KB_RESET":
                        reset_defaults()
                        self._kb_listening = None
                    elif action == "PRE_SOLO":
                        self.selected_mode = "SOLO"
                        self.state = "MENU_SOLO_TYPE"
                    elif action == "SELECT_SOLO_1V0":
                        self.selected_solo_type = "1v0"
                        self.state = "MENU_STAGE"
                    elif action == "SELECT_SOLO_1V1":
                        self.selected_solo_type = "1v1"
                        self.state = "MENU_STAGE"
                    elif action == "SELECT_SOLO_1VBOT":
                        self.selected_solo_type = "1vBot"
                        self.state = "MENU_DIFF_BOT"
                    elif action == "SELECT_DIFF_EASY":
                        self.selected_bot_difficulty = "EASY"
                        self.state = "MENU_STAGE"
                    elif action == "SELECT_DIFF_NORMAL":
                        self.selected_bot_difficulty = "NORMAL"
                        self.state = "MENU_STAGE"
                    elif action == "SELECT_DIFF_HARD":
                        self.selected_bot_difficulty = "HARD"
                        self.state = "MENU_STAGE"
                    elif action == "BACK_TO_SOLO_TYPE":
                        self.state = "MENU_SOLO_TYPE"
                    elif action == "PRE_HOST":
                        self.selected_mode = "HOST"
                        self.state = "MENU_STAGE"
                    elif action == "PRE_JOIN":
                        self.selected_mode = "CLIENT"
                        self.selected_ip = self.ip_box.text
                        self.state = "MENU_CHAR"
                    elif action.startswith("SELECT_STAGE_"):
                        idx = int(action.split("_")[-1])
                        self.selected_stage = self.available_stages[idx]
                        if self.selected_mode == "SOLO" and self.selected_solo_type == "1v1":
                            self.state = "MENU_CHAR_P1"
                        elif self.selected_mode == "SOLO" and self.selected_solo_type == "1vBot":
                            self.state = "MENU_CHAR"   # P1 choisit son perso, le bot aura le sien après
                        else:
                            self.state = "MENU_CHAR"
                    elif action == "BACK_TO_PREV":
                        if self.selected_mode == "SOLO" and self.selected_solo_type == "1vBot":
                            self.state = "MENU_DIFF_BOT"
                        elif self.selected_mode == "SOLO":
                            self.state = "MENU_SOLO_TYPE"
                        else:
                            self.state = "MENU_MAIN"
                    elif action.startswith("SELECT_CHAR_BOT_"):
                        idx = int(action.split("_")[-1])
                        bot_char = self.available_chars[idx]["id"]
                        return {
                            'action': 'GAME',
                            'mode': self.selected_mode,
                            'ip': self.selected_ip,
                            'stage': self.selected_stage,
                            'character_class': self.selected_char_p1,
                            'character_class_p2': bot_char,
                            'solo_mode': self.selected_solo_type,
                            'bot_difficulty': self.selected_bot_difficulty,
                        }
                    elif action.startswith("SELECT_CHAR_P2_"):
                        idx = int(action.split("_")[-1])
                        self.selected_char_p2 = self.available_chars[idx]["id"]
                        return {
                            'action': 'GAME',
                            'mode': self.selected_mode,
                            'ip': self.selected_ip,
                            'stage': self.selected_stage,
                            'character_class': self.selected_char_p1,
                            'character_class_p2': self.selected_char_p2,
                            'solo_mode': self.selected_solo_type,
                            'bot_difficulty': self.selected_bot_difficulty,
                        }
                    elif action.startswith("SELECT_CHAR_"):
                        idx = int(action.split("_")[-1])
                        self.selected_char_id = self.available_chars[idx]["id"]
                        if self.state == "MENU_CHAR_P1":
                            self.selected_char_p1 = self.selected_char_id
                            self.state = "MENU_CHAR_P2"
                        elif self.selected_mode == "SOLO" and self.selected_solo_type == "1vBot":
                            self.selected_char_p1 = self.selected_char_id
                            self.state = "MENU_CHAR_BOT"
                        else:
                            return {
                                'action': 'GAME',
                                'mode': self.selected_mode,
                                'ip': self.selected_ip,
                                'stage': self.selected_stage,
                                'character_class': self.selected_char_id,
                                'character_class_p2': None,
                                'solo_mode': self.selected_solo_type,
                                'bot_difficulty': self.selected_bot_difficulty,
                            }
                    elif action == "BACK_TO_CHAR_P1":
                        self.state = "MENU_CHAR_P1"
                    elif action == "BACK_TO_CHAR_P1_BOT":
                        self.state = "MENU_CHAR"
                    elif action == "BACK_TO_STAGE":
                        if self.selected_mode == "CLIENT":
                            self.state = "MENU_MULTI"
                        else:
                            self.state = "MENU_STAGE"

            # ----------------------------------------------------------------
            # AFFICHAGE
            # ----------------------------------------------------------------
            if self.state == "MENU_MAIN":
                draw_text_centered(surface_to_draw, "RIFT FIGHTERS", 100, size=70, color=(0, 255, 200))

            elif self.state == "MENU_MULTI":
                draw_text_centered(surface_to_draw, "MODE EN LIGNE", 100)
                draw_text_centered(surface_to_draw, "IP du Host (Rejoindre):", 280, size=20)
                self.ip_box.draw(surface_to_draw)

            elif self.state == "MENU_SOLO_TYPE":
                draw_text_centered(surface_to_draw, "MODE ENTRAÎNEMENT", 80, size=50, color=(255, 200, 50))
                font = pygame.font.SysFont("Consolas", 18)
                for txt, y, color in [
                    ("Entraînez-vous seul contre la gravité", 170, (150, 150, 150)),
                    ("Affrontez un adversaire local (même clavier)", 250, (150, 150, 150)),
                ]:
                    s = font.render(txt, True, color)
                    surface_to_draw.blit(s, (self.width // 2 - s.get_width() // 2, y))

                cx = self.width // 2
                font_key = pygame.font.SysFont("Consolas", 16, bold=True)
                p1_keys = [
                    ("Déplacer",  "Q / D",    (220, 220, 220)),
                    ("Sauter",    "ESPACE",    (220, 220, 220)),
                    ("Attaquer",  "G",         (255, 180,  80)),
                    ("Bouclier",  "N",         (100, 180, 255)),
                    ("Dash",      "2x ← ou →", (255, 160,  30)),
                ]
                p2_keys = [
                    ("Déplacer",  "← / →",    (220, 220, 220)),
                    ("Sauter",    "↑",         (220, 220, 220)),
                    ("Attaquer",  "ENTRÉE",    (255, 180,  80)),
                    ("Bouclier",  "M",         (100, 180, 255)),
                    ("Dash",      "2x ← ou →", (255, 160,  30)),
                ]
                p1_x, p2_x, y_keys = cx - 280, cx + 80, 370
                surface_to_draw.blit(font.render("── Joueur 1 ──", True, (100, 255, 100)), (p1_x, y_keys - 22))
                surface_to_draw.blit(font.render("── Joueur 2 ──", True, (255, 150, 150)), (p2_x, y_keys - 22))
                for (l1, k1, c1), (l2, k2, c2) in zip(p1_keys, p2_keys):
                    surface_to_draw.blit(font_key.render(f"{l1}: {k1}", True, c1), (p1_x, y_keys))
                    surface_to_draw.blit(font_key.render(f"{l2}: {k2}", True, c2), (p2_x, y_keys))
                    y_keys += 22

            elif self.state == "MENU_STAGE":
                draw_text_centered(surface_to_draw, "CHOIX DU STAGE", 80)
                self.draw_stage_preview(surface_to_draw, self.hovered_stage_idx)

            elif self.state == "MENU_CHAR_P1":
                draw_text_centered(surface_to_draw, "JOUEUR 1 — CHOIX DU COMBATTANT", 80, size=36, color=(100, 255, 100))
                self.draw_character_preview(surface_to_draw, self.hovered_char_idx, side="left")

            elif self.state == "MENU_CHAR_P2":
                draw_text_centered(surface_to_draw, "JOUEUR 2 — CHOIX DU COMBATTANT", 80, size=36, color=(255, 100, 100))
                p1_idx = self._get_char_idx_by_id(self.selected_char_p1)
                self.draw_character_preview(surface_to_draw, p1_idx, side="left")
                self.draw_character_preview(surface_to_draw, self.hovered_char_idx, side="right")

            elif self.state == "MENU_CHAR":
                draw_text_centered(surface_to_draw, "CHOIX DU COMBATTANT", 80)
                self.draw_character_preview(surface_to_draw, self.hovered_char_idx, side="left")

            elif self.state == "MENU_CHAR_BOT":
                draw_text_centered(surface_to_draw, "PERSO DU BOT", 80, size=36, color=(255, 120, 30))
                p1_idx = self._get_char_idx_by_id(self.selected_char_p1)
                self.draw_character_preview(surface_to_draw, p1_idx, side="left")
                self.draw_character_preview(surface_to_draw, self.hovered_char_idx, side="right")

            elif self.state == "MENU_DIFF_BOT":
                draw_text_centered(surface_to_draw, "DIFFICULTÉ DU BOT", 80, size=50, color=(255, 120, 30))
                font_desc = pygame.font.SysFont("Consolas", 17)
                descs = [
                    (190, "Réactions lentes, erreurs fréquentes, n'utilise pas le bouclier", (100, 200, 100)),
                    (275, "Réactions correctes, attaques à portée, bloque parfois",           (220, 180, 50)),
                    (360, "Réactions rapides, punit les recoveries, dash et double saut",      (220, 80,  80)),
                ]
                for dy, txt, col in descs:
                    s = font_desc.render(txt, True, col)
                    surface_to_draw.blit(s, (self.width // 2 - s.get_width() // 2, dy))

            elif self.state == "RULES":
                self.draw_rules(surface_to_draw)

            elif self.state == "MENU_KEYBINDINGS":
                self.draw_keybindings_screen(surface_to_draw)

            # ----------------------------------------------------------------
            # BOUTONS
            # ----------------------------------------------------------------
            if not self.popup_error:
                if self.state == "MENU_STAGE":
                    clip_rect = pygame.Rect(
                        self.stage_start_x - 10, self.stage_start_y - 10,
                        self.stage_columns * (self.stage_button_width + self.stage_padding) + 20,
                        self.height - self.stage_start_y - 110
                    )
                    original_clip = surface_to_draw.get_clip()
                    surface_to_draw.set_clip(clip_rect)
                    for btn in self.stage_buttons:
                        original_y = btn.rect.y
                        btn.rect.y += self.stage_scroll_offset
                        if btn.rect.y + btn.rect.height > self.stage_start_y - 10 and btn.rect.y < clip_rect.bottom:
                            btn.draw(surface_to_draw)
                        btn.rect.y = original_y
                    surface_to_draw.set_clip(original_clip)
                    self.btn_stage_back.draw(surface_to_draw)

                    num_rows = (len(self.available_stages) + self.stage_columns - 1) // self.stage_columns
                    total_height = num_rows * (self.stage_button_height + self.stage_padding)
                    visible_height = self.height - self.stage_start_y - 120
                    if total_height > visible_height:
                        scrollbar_x = clip_rect.right + 10
                        scrollbar_height = clip_rect.height
                        scrollbar_y = clip_rect.top
                        pygame.draw.rect(surface_to_draw, (50, 50, 50), (scrollbar_x, scrollbar_y, 10, scrollbar_height), border_radius=5)
                        scroll_ratio = abs(self.stage_scroll_offset) / (total_height - visible_height)
                        cursor_height = max(30, scrollbar_height * (visible_height / total_height))
                        cursor_y = scrollbar_y + scroll_ratio * (scrollbar_height - cursor_height)
                        pygame.draw.rect(surface_to_draw, (150, 150, 150), (scrollbar_x, cursor_y, 10, cursor_height), border_radius=5)
                else:
                    if self.state == "MENU_KEYBINDINGS":
                        # Les onglets P1/P2 sont dessinés dans draw_keybindings_screen
                        self.btn_kb_back.draw(surface_to_draw)
                        self.btn_kb_reset.draw(surface_to_draw)
                    else:
                        for btn in active_buttons:
                            btn.draw(surface_to_draw)

            # ----------------------------------------------------------------
            # POPUP ERREUR
            # ----------------------------------------------------------------
            if self.popup_error:
                overlay = pygame.Surface((self.width, self.height))
                overlay.set_alpha(200)
                overlay.fill((0, 0, 0))
                surface_to_draw.blit(overlay, (0, 0))
                rect_popup = pygame.Rect(self.width // 2 - 250, 200, 500, 250)
                pygame.draw.rect(surface_to_draw, (50, 0, 0), rect_popup, border_radius=12)
                pygame.draw.rect(surface_to_draw, (255, 50, 50), rect_popup, 3, border_radius=12)
                draw_text_centered(surface_to_draw, "ERREUR", 230, size=40, color=(255, 100, 100))
                msg_surf = pygame.font.SysFont("Consolas", 20).render(str(self.popup_error), True, (255, 255, 255))
                surface_to_draw.blit(msg_surf, msg_surf.get_rect(center=(self.width // 2, 290)))
                self.btn_popup_ok.draw(surface_to_draw)

            # ----------------------------------------------------------------
            # RENDU FINAL
            # ----------------------------------------------------------------
            render_engine.screen.fill((0, 0, 0))
            target_w = int(render_engine.logical_width * render_engine.scale)
            target_h = int(render_engine.logical_height * render_engine.scale)
            scaled = pygame.transform.scale(surface_to_draw, (target_w, target_h))
            render_engine.screen.blit(scaled, (render_engine.offset_x, render_engine.offset_y))
            pygame.display.flip()
            self.clock.tick(30)