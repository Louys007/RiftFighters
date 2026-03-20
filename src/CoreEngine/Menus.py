import pygame
import os


def draw_text_centered(surface, text, y, size=40, color=(255, 255, 255)):
    font = pygame.font.SysFont("Arial", size, bold=True)
    txt_surf = font.render(text, True, color)
    rect = txt_surf.get_rect(center=(surface.get_width() // 2, y))
    surface.blit(txt_surf, rect)


class Button:
    def __init__(self, x, y, width, height, text, action_code, color=(50, 150, 255), hover_color=(70, 170, 255),
                 text_color=(255, 255, 255), image_path=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action_code = action_code
        self.base_color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.font = pygame.font.SysFont("Arial", 24, bold=True)
        self.is_hovered = False
        self.image_path = image_path

        self.image = None
        if image_path and os.path.exists(image_path):
            try:
                img_raw = pygame.image.load(image_path)
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
        if self.image:
            surface.blit(self.image, self.rect)
            if self.is_hovered:
                pygame.draw.rect(surface, (255, 255, 255), self.rect, 4, border_radius=8)
            text_surf = self.font.render(self.text, True, self.text_color)
            text_rect = text_surf.get_rect(center=self.rect.center)
            shadow_surf = self.font.render(self.text, True, (0, 0, 0))
            surface.blit(shadow_surf, (text_rect.x + 2, text_rect.y + 2))
            surface.blit(text_surf, text_rect)
        else:
            color = self.hover_color if self.is_hovered else self.base_color
            pygame.draw.rect(surface, color, self.rect, border_radius=8)
            pygame.draw.rect(surface, (255, 255, 255), self.rect, 2, border_radius=8)
            text_surf = self.font.render(self.text, True, self.text_color)
            text_rect = text_surf.get_rect(center=self.rect.center)
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
        self.available_stages = ["Lab.png", "Cave.png", "Futur.png", "FarWest.png"]

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
            Button(bx, 450, bw, 50, "Quitter", "QUIT", color=(200, 50, 50), hover_color=(255, 50, 50))
        ]

        bw_solo = 300
        bx_solo = cx - bw_solo // 2
        self.solo_type_buttons = [
            Button(bx_solo, 200, bw_solo, 60, "1v0 - Solo", "SELECT_SOLO_1V0", color=(100, 150, 255)),
            Button(bx_solo, 280, bw_solo, 60, "1v1 - Local", "SELECT_SOLO_1V1", color=(150, 100, 255)),
            Button(bx_solo, 400, 200, 50, "Retour", "BACK")
        ]

        self.multi_buttons = [
            Button(bx, 200, bw, 50, "Héberger (Host)", "PRE_HOST"),
            Button(bx, 360, bw, 50, "Rejoindre IP", "PRE_JOIN"),
            Button(bx, 500, bw, 50, "Retour", "BACK")
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

        self.btn_back = Button(bx, 500, bw, 50, "Retour", "BACK")

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

        pygame.draw.rect(surface, (50, 50, 50), (preview_x - 10, preview_y - 40, preview_w + 20, preview_h + 80), border_radius=10)
        pygame.draw.rect(surface, (255, 200, 50), (preview_x - 10, preview_y - 40, preview_w + 20, preview_h + 80), 3, border_radius=10)

        font = pygame.font.SysFont("Arial", 20, bold=True)
        title_surf = font.render("APERÇU DU STAGE", True, (255, 200, 50))
        surface.blit(title_surf, (preview_x + preview_w // 2 - title_surf.get_width() // 2, preview_y - 30))

        preview_img = self.load_preview_image(img_path, (preview_w, preview_h))
        if preview_img:
            surface.blit(preview_img, (preview_x, preview_y))
        else:
            pygame.draw.rect(surface, (30, 30, 30), (preview_x, preview_y, preview_w, preview_h))
            no_img_text = font.render("Image non disponible", True, (150, 150, 150))
            surface.blit(no_img_text, (preview_x + preview_w // 2 - no_img_text.get_width() // 2, preview_y + preview_h // 2))

        name_surf = font.render(stage_name, True, (200, 200, 200))
        surface.blit(name_surf, (preview_x + preview_w // 2 - name_surf.get_width() // 2, preview_y + preview_h + 10))

    def draw_character_preview(self, surface, char_idx, side="left"):
        if char_idx is None:
            return

        char_data = self.available_chars[char_idx]
        preview_w = 350
        preview_h = 400

        if side == "left":
            preview_x = 50
            player_label = "JOUEUR 1"
            player_color = (100, 255, 100)
        else:
            preview_x = self.width - preview_w - 50
            player_label = "JOUEUR 2"
            player_color = (255, 100, 100)

        preview_y = 150

        pygame.draw.rect(surface, (50, 50, 50), (preview_x - 10, preview_y - 60, preview_w + 20, preview_h + 100), border_radius=10)
        pygame.draw.rect(surface, char_data["color"], (preview_x - 10, preview_y - 60, preview_w + 20, preview_h + 100), 3, border_radius=10)

        font_small = pygame.font.SysFont("Arial", 16, bold=True)
        player_surf = font_small.render(player_label, True, player_color)
        surface.blit(player_surf, (preview_x + preview_w // 2 - player_surf.get_width() // 2, preview_y - 50))

        font = pygame.font.SysFont("Arial", 18, bold=True)
        title_surf = font.render("APERÇU", True, char_data["color"])
        surface.blit(title_surf, (preview_x + preview_w // 2 - title_surf.get_width() // 2, preview_y - 30))

        name_font = pygame.font.SysFont("Arial", 28, bold=True)
        name_surf = name_font.render(char_data["name"], True, (255, 255, 255))
        surface.blit(name_surf, (preview_x + preview_w // 2 - name_surf.get_width() // 2, preview_y + 15))

        cube_size = 120
        cube_x = preview_x + preview_w // 2 - cube_size // 2
        cube_y = preview_y + 70

        img_path = os.path.join("assets", "Perso", char_data["image"])
        preview_img = self.load_preview_image(img_path, (cube_size, cube_size))

        if preview_img:
            surface.blit(preview_img, (cube_x, cube_y))
        else:
            pygame.draw.rect(surface, char_data["color"], (cube_x, cube_y, cube_size, cube_size), border_radius=15)

        pygame.draw.rect(surface, (255, 255, 255), (cube_x, cube_y, cube_size, cube_size), 4, border_radius=15)

        stats_y = cube_y + cube_size + 30
        stats_font = pygame.font.SysFont("Arial", 16)
        stats_list = [
            f"Vitesse: {char_data['stats']['speed']}",
            f"Saut: {abs(char_data['stats']['jump'])}",
            f"Gravité: {char_data['stats']['gravity']}"
        ]
        for i, stat in enumerate(stats_list):
            stat_surf = stats_font.render(stat, True, (200, 200, 200))
            surface.blit(stat_surf, (preview_x + 30, stats_y + i * 28))

    # ------------------------------------------------------------------ #
    #  RÈGLES
    # ------------------------------------------------------------------ #

    def draw_rules(self, surface):
        draw_text_centered(surface, "RÈGLES & CONTRÔLES", 50, size=45, color=(255, 200, 50))

        font_title = pygame.font.SysFont("Arial", 22, bold=True)
        font_line  = pygame.font.SysFont("Arial", 18)
        font_small = pygame.font.SysFont("Arial", 15)

        cx = self.width // 2

        draw_text_centered(surface, "── Règles ──", 110, size=20, color=(200, 200, 200))
        general = [
            "Réduisez la vie de l'adversaire à 0 pour gagner",
            "Si le temps est écoulé, le joueur avec le plus de vie gagne",
            "En multijoueur, l'Hôte lance la partie en premier",
        ]
        for i, line in enumerate(general):
            surf = font_small.render(line, True, (160, 160, 160))
            surface.blit(surf, (cx - surf.get_width() // 2, 135 + i * 20))

        # --- Colonne gauche — Joueur 1 ---
        col_x_left = 80
        y = 210

        p1_title = font_title.render("JOUEUR 1", True, (100, 255, 100))
        surface.blit(p1_title, (col_x_left, y))
        y += 35

        common_p1 = [
            ("Déplacer",  "Q  /  D",  (220, 220, 220)),
            ("Sauter",    "ESPACE",   (220, 220, 220)),
            ("Attaquer",  "G",        (255, 180,  80)),
            ("Bouclier",  "N",        (100, 180, 255)),
            ("Dash",      "2x ← ou →",(255, 160,  30)),
        ]
        for label, key, color in common_p1:
            surface.blit(font_line.render(f"{label} :", True, (180, 180, 180)), (col_x_left, y))
            surface.blit(font_line.render(key, True, color), (col_x_left + 130, y))
            y += 26

        y += 15
        crom_title = font_title.render("Cromagnon", True, (0, 220, 0))
        surface.blit(crom_title, (col_x_left, y))
        y += 28
        for line in ["Lance sa lance vers l'avant", "Attaque mêlée courte portée", "Dégâts : 12 pts"]:
            surface.blit(font_small.render(line, True, (140, 200, 140)), (col_x_left, y))
            y += 20

        y += 10
        robot_title = font_title.render("Robot", True, (255, 100, 100))
        surface.blit(robot_title, (col_x_left, y))
        y += 28
        for line in ["Tire une boule d'énergie", "Attaque à distance", "Dégâts : 18 pts  |  1 boule à la fois"]:
            surface.blit(font_small.render(line, True, (200, 140, 140)), (col_x_left, y))
            y += 20

        y += 10
        sam_title = font_title.render("Samouraï", True, (180, 100, 255))
        surface.blit(sam_title, (col_x_left, y))
        y += 28
        for line in ["Tranche avec son katana", "Attaque mêlée rapide, longue portée", "Dégâts : 15 pts"]:
            surface.blit(font_small.render(line, True, (180, 150, 220)), (col_x_left, y))
            y += 20

        # --- Colonne droite — Joueur 2 ---
        col_x_right = cx + 80
        y = 210

        p2_title = font_title.render("JOUEUR 2", True, (255, 150, 150))
        surface.blit(p2_title, (col_x_right, y))
        y += 35

        common_p2 = [
            ("Déplacer",  "← / →",    (220, 220, 220)),
            ("Sauter",    "↑",         (220, 220, 220)),
            ("Attaquer",  "ENTRÉE",    (255, 180,  80)),
            ("Bouclier",  "M",         (100, 180, 255)),
            ("Dash",      "2x ← ou →", (255, 160,  30)),
        ]
        for label, key, color in common_p2:
            surface.blit(font_line.render(f"{label} :", True, (180, 180, 180)), (col_x_right, y))
            surface.blit(font_line.render(key, True, color), (col_x_right + 130, y))
            y += 26

        # Séparateur vertical
        pygame.draw.line(surface, (80, 80, 80), (cx, 200), (cx, 580), 1)

        # --- Bas — Bouclier ---
        shield_y = 555
        draw_text_centered(surface, "── Bouclier ──", shield_y, size=18, color=(100, 180, 255))
        for i, line in enumerate([
            "Bloque 80% des dégâts (mêlée ET projectile)  —  Uniquement au sol, hors attaque",
            "Après relâchement : 30 frames de stun (barre bleue au-dessus du perso)",
        ]):
            surf = font_small.render(line, True, (120, 160, 220))
            surface.blit(surf, (cx - surf.get_width() // 2, shield_y + 25 + i * 18))

        # --- Bas — Dash ---
        dash_y = shield_y + 70
        draw_text_centered(surface, "── Dash ──", dash_y, size=18, color=(255, 160, 30))
        for i, line in enumerate([
            "Double-tap ← ou → pour dasher dans cette direction  —  Au sol et en l'air",
            "Impossible pendant une attaque ou un bouclier  —  Les persos se traversent pendant le dash",
            "Cooldown : barre orange sous le personnage",
        ]):
            surf = font_small.render(line, True, (220, 150, 80))
            surface.blit(surf, (cx - surf.get_width() // 2, dash_y + 25 + i * 18))

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

    def run(self, render_engine):
        running = True
        surface_to_draw = render_engine.internal_surface

        while running:
            surface_to_draw.fill((30, 30, 30))
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
            elif self.state in ("MENU_CHAR_P1", "MENU_CHAR", "MENU_CHAR_P2"):
                btns = self.char_buttons if self.state != "MENU_CHAR_P2" else self.char_buttons_p2
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
                        self.state = "MENU_MAIN"
                    elif action == "GO_MULTI_MENU":
                        self.state = "MENU_MULTI"
                    elif action == "GO_RULES":
                        self.state = "RULES"
                    elif action == "PRE_SOLO":
                        self.selected_mode = "SOLO"
                        self.state = "MENU_SOLO_TYPE"
                    elif action == "SELECT_SOLO_1V0":
                        self.selected_solo_type = "1v0"
                        self.state = "MENU_STAGE"
                    elif action == "SELECT_SOLO_1V1":
                        self.selected_solo_type = "1v1"
                        self.state = "MENU_STAGE"
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
                        else:
                            self.state = "MENU_CHAR"
                    elif action == "BACK_TO_PREV":
                        if self.selected_mode == "SOLO":
                            self.state = "MENU_SOLO_TYPE"
                        else:
                            self.state = "MENU_MAIN"
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
                            'solo_mode': self.selected_solo_type
                        }
                    elif action.startswith("SELECT_CHAR_"):
                        idx = int(action.split("_")[-1])
                        self.selected_char_id = self.available_chars[idx]["id"]
                        if self.state == "MENU_CHAR_P1":
                            self.selected_char_p1 = self.selected_char_id
                            self.state = "MENU_CHAR_P2"
                        else:
                            return {
                                'action': 'GAME',
                                'mode': self.selected_mode,
                                'ip': self.selected_ip,
                                'stage': self.selected_stage,
                                'character_class': self.selected_char_id,
                                'character_class_p2': None,
                                'solo_mode': self.selected_solo_type
                            }
                    elif action == "BACK_TO_CHAR_P1":
                        self.state = "MENU_CHAR_P1"
                    elif action == "BACK_TO_STAGE":
                        if self.selected_mode == "CLIENT":
                            self.state = "MENU_MULTI"
                        else:
                            self.state = "MENU_STAGE"

            # ----------------------------------------------------------------
            # AFFICHAGE
            # ----------------------------------------------------------------
            if self.state == "MENU_MAIN":
                draw_text_centered(surface_to_draw, "RIFT FIGHTERS", 100, size=60, color=(255, 200, 50))

            elif self.state == "MENU_MULTI":
                draw_text_centered(surface_to_draw, "MODE EN LIGNE", 100)
                draw_text_centered(surface_to_draw, "IP du Host (Rejoindre):", 280, size=20)
                self.ip_box.draw(surface_to_draw)

            elif self.state == "MENU_SOLO_TYPE":
                draw_text_centered(surface_to_draw, "MODE ENTRAÎNEMENT", 80, size=50, color=(255, 200, 50))
                font = pygame.font.SysFont("Arial", 18)
                for txt, y, color in [
                    ("Entraînez-vous seul contre la gravité", 170, (150, 150, 150)),
                    ("Affrontez un adversaire local (même clavier)", 250, (150, 150, 150)),
                ]:
                    s = font.render(txt, True, color)
                    surface_to_draw.blit(s, (self.width // 2 - s.get_width() // 2, y))

                cx = self.width // 2
                font_key = pygame.font.SysFont("Arial", 16, bold=True)
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

            elif self.state == "RULES":
                self.draw_rules(surface_to_draw)

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
                msg_surf = pygame.font.SysFont("Arial", 20).render(str(self.popup_error), True, (255, 255, 255))
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