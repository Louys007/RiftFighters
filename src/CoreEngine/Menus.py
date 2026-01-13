import pygame
import os
from ..Entities.Player import CubeFighter, RedStriker


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
        self.image_path = image_path  # Stocke le chemin pour la preview

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

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
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
                    if len(self.text) < 20: self.text += event.unicode
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
        self.selected_stage = "stage_labo.png"
        self.selected_char_class = CubeFighter

        self.available_stages = ["stage_labo.png","Cave.png", "Futur.png","FarWest.png"]
        self.available_chars = [CubeFighter, RedStriker]

        # --- PREVIEW SYSTEM ---
        self.preview_cache = {}  # Cache des images de preview
        self.hovered_stage_idx = None
        self.hovered_char_idx = None

        # --- CALCUL DU CENTRAGE ---
        cx = width // 2

        # Largeur boutons standards
        bw = 200
        bx = cx - bw // 2

        self.main_buttons = [
            Button(bx, 200, bw, 50, "Entraînement", "PRE_SOLO"),
            Button(bx, 270, bw, 50, "Multijoueur", "GO_MULTI_MENU"),
            Button(bx, 340, bw, 50, "Règles", "GO_RULES"),
            Button(bx, 450, bw, 50, "Quitter", "QUIT", color=(200, 50, 50), hover_color=(255, 50, 50))
        ]

        self.multi_buttons = [
            Button(bx, 200, bw, 50, "Héberger (Host)", "PRE_HOST"),
            Button(bx, 360, bw, 50, "Rejoindre IP", "PRE_JOIN"),
            Button(bx, 500, bw, 50, "Retour", "BACK")
        ]
        self.ip_box = InputBox(bx, 300, bw, 40, "localhost")

        # Boutons Stages - GRILLE ADAPTATIVE
        self.stage_scroll_offset = 0  # Pour le scroll
        self.stage_buttons = []
        self.stage_button_width = 280
        self.stage_button_height = 140
        self.stage_columns = 2  # 2 colonnes
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
        self.btn_stage_back = Button(50, height - 100, 150, 50, "Retour", "BACK_TO_MAIN")

        # Boutons personnages - CENTRÉS (pour avoir preview à gauche ET à droite)
        bw_char = 300
        bx_char = cx - bw_char // 2
        self.char_buttons = []
        for i, char_cls in enumerate(self.available_chars):
            self.char_buttons.append(
                Button(bx_char, 150 + i * 70, bw_char, 60, char_cls.CLASS_NAME, f"SELECT_CHAR_{i}", color=char_cls.MENU_COLOR)
            )
        self.btn_char_back = Button(50, height - 100, 150, 50, "Retour", "BACK_TO_STAGE")
        self.btn_back = Button(bx, 500, bw, 50, "Retour", "BACK")

    def load_preview_image(self, path, target_size):
        """Charge et met en cache une image de preview"""
        if path not in self.preview_cache:
            try:
                img = pygame.image.load(path)
                img = pygame.transform.scale(img, target_size)
                self.preview_cache[path] = img
            except Exception as e:
                print(f"Erreur chargement preview {path}: {e}")
                self.preview_cache[path] = None
        return self.preview_cache[path]

    def draw_stage_preview(self, surface, stage_idx):
        """Affiche une grande preview du stage survolé"""
        if stage_idx is None:
            return
        
        stage_name = self.available_stages[stage_idx]
        img_path = os.path.join("assets", "Stages", stage_name)
        
        # Zone de preview à droite
        preview_x = 750
        preview_y = 150
        preview_w = 450
        preview_h = 300
        
        # Cadre de preview
        pygame.draw.rect(surface, (50, 50, 50), (preview_x - 10, preview_y - 40, preview_w + 20, preview_h + 80), border_radius=10)
        pygame.draw.rect(surface, (255, 200, 50), (preview_x - 10, preview_y - 40, preview_w + 20, preview_h + 80), 3, border_radius=10)
        
        # Titre
        font = pygame.font.SysFont("Arial", 20, bold=True)
        title_surf = font.render("APERÇU DU STAGE", True, (255, 200, 50))
        surface.blit(title_surf, (preview_x + preview_w // 2 - title_surf.get_width() // 2, preview_y - 30))
        
        # Image
        preview_img = self.load_preview_image(img_path, (preview_w, preview_h))
        if preview_img:
            surface.blit(preview_img, (preview_x, preview_y))
        else:
            # Fallback si pas d'image
            pygame.draw.rect(surface, (30, 30, 30), (preview_x, preview_y, preview_w, preview_h))
            no_img_text = font.render("Image non disponible", True, (150, 150, 150))
            surface.blit(no_img_text, (preview_x + preview_w // 2 - no_img_text.get_width() // 2, preview_y + preview_h // 2))
        
        # Nom du stage en bas
        name_surf = font.render(stage_name, True, (200, 200, 200))
        surface.blit(name_surf, (preview_x + preview_w // 2 - name_surf.get_width() // 2, preview_y + preview_h + 10))

    def draw_character_preview(self, surface, char_idx, side="left"):
        """Affiche une grande preview du personnage survolé
        side: "left" pour P1, "right" pour P2
        """
        if char_idx is None:
            return
        
        char_cls = self.available_chars[char_idx]
        
        # Zone de preview - GAUCHE ou DROITE selon le côté
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
        
        # Cadre de preview
        pygame.draw.rect(surface, (50, 50, 50), (preview_x - 10, preview_y - 60, preview_w + 20, preview_h + 100), border_radius=10)
        pygame.draw.rect(surface, char_cls.MENU_COLOR, (preview_x - 10, preview_y - 60, preview_w + 20, preview_h + 100), 3, border_radius=10)
        
        # Label du joueur (P1 ou P2)
        font_small = pygame.font.SysFont("Arial", 16, bold=True)
        player_surf = font_small.render(player_label, True, player_color)
        surface.blit(player_surf, (preview_x + preview_w // 2 - player_surf.get_width() // 2, preview_y - 50))
        
        # Titre
        font = pygame.font.SysFont("Arial", 18, bold=True)
        title_surf = font.render("APERÇU", True, char_cls.MENU_COLOR)
        surface.blit(title_surf, (preview_x + preview_w // 2 - title_surf.get_width() // 2, preview_y - 30))
        
        # Nom du personnage
        name_font = pygame.font.SysFont("Arial", 28, bold=True)
        name_surf = name_font.render(char_cls.CLASS_NAME, True, (255, 255, 255))
        surface.blit(name_surf, (preview_x + preview_w // 2 - name_surf.get_width() // 2, preview_y + 15))
        
        # Représentation visuelle du personnage (cube géant)
        cube_size = 120
        cube_x = preview_x + preview_w // 2 - cube_size // 2
        cube_y = preview_y + 70
        pygame.draw.rect(surface, char_cls.MENU_COLOR, (cube_x, cube_y, cube_size, cube_size), border_radius=15)
        pygame.draw.rect(surface, (255, 255, 255), (cube_x, cube_y, cube_size, cube_size), 4, border_radius=15)
        
        # Stats du personnage
        temp_char = char_cls(0, 0)
        stats_y = cube_y + cube_size + 30
        stats_font = pygame.font.SysFont("Arial", 16)
        
        stats = [
            f"Vitesse: {temp_char.speed}",
            f"Saut: {abs(temp_char.jump_strength)}",
            f"Gravité: {temp_char.gravity}"
        ]
        
        for i, stat in enumerate(stats):
            stat_surf = stats_font.render(stat, True, (200, 200, 200))
            surface.blit(stat_surf, (preview_x + 30, stats_y + i * 28))

    def show_error(self, message):
        self.popup_error = message
        self.state = "MENU_MAIN"

    def run(self, render_engine):
        running = True
        surface_to_draw = render_engine.internal_surface

        while running:
            surface_to_draw.fill((30, 30, 30))
            mouse_pos = render_engine.get_virtual_mouse_pos()

            # Reset hover tracking
            self.hovered_stage_idx = None
            self.hovered_char_idx = None

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
                elif self.state == "MENU_STAGE":
                    active_buttons = self.stage_buttons + [self.btn_stage_back]
                elif self.state == "MENU_CHAR":
                    active_buttons = self.char_buttons + [self.btn_char_back]

            for btn in active_buttons:
                btn.check_hover(mouse_pos)

            # Détection du hover pour les previews
            if self.state == "MENU_STAGE":
                for i, btn in enumerate(self.stage_buttons):
                    # Ajuster la position du bouton avec le scroll
                    adjusted_rect = pygame.Rect(btn.rect.x, btn.rect.y + self.stage_scroll_offset, btn.rect.width, btn.rect.height)
                    if adjusted_rect.collidepoint(mouse_pos):
                        btn.is_hovered = True
                        self.hovered_stage_idx = i
                        break
                    else:
                        btn.is_hovered = False
            elif self.state == "MENU_CHAR":
                for i, btn in enumerate(self.char_buttons):
                    if btn.is_hovered:
                        self.hovered_char_idx = i
                        break

            action = None
            for event in pygame.event.get():
                if event.type == pygame.QUIT: return {'action': 'QUIT'}

                if event.type == pygame.VIDEORESIZE:
                    render_engine.update_scale_factors()
                
                # Gestion du scroll pour les stages
                if self.state == "MENU_STAGE" and event.type == pygame.MOUSEWHEEL:
                    # Calculer le nombre de lignes nécessaires
                    num_rows = (len(self.available_stages) + self.stage_columns - 1) // self.stage_columns
                    total_height = num_rows * (self.stage_button_height + self.stage_padding)
                    visible_height = self.height - self.stage_start_y - 120  # Espace pour le titre et le bouton retour
                    
                    # Scroll uniquement si le contenu dépasse
                    if total_height > visible_height:
                        scroll_speed = 30
                        self.stage_scroll_offset += event.y * scroll_speed
                        # Limites du scroll
                        max_scroll = 0
                        min_scroll = -(total_height - visible_height)
                        self.stage_scroll_offset = max(min_scroll, min(max_scroll, self.stage_scroll_offset))

                if self.state == "MENU_MULTI" and not self.popup_error:
                    self.ip_box.handle_event(event)

                for btn in active_buttons:
                    res = btn.handle_event(event)
                    if res: action = res

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
                        self.state = "MENU_CHAR"
                    elif action == "BACK_TO_MAIN":
                        self.state = "MENU_MAIN"

                    elif action.startswith("SELECT_CHAR_"):
                        idx = int(action.split("_")[-1])
                        self.selected_char_class = self.available_chars[idx]
                        return {
                            'action': 'GAME',
                            'mode': self.selected_mode,
                            'ip': self.selected_ip,
                            'stage': self.selected_stage,
                            'character_class': self.selected_char_class
                        }
                    elif action == "BACK_TO_STAGE":
                        if self.selected_mode == "CLIENT":
                            self.state = "MENU_MULTI"
                        else:
                            self.state = "MENU_STAGE"

            if self.state == "MENU_MAIN":
                draw_text_centered(surface_to_draw, "RIFT FIGHTERS", 100, size=60, color=(255, 200, 50))
            elif self.state == "MENU_MULTI":
                draw_text_centered(surface_to_draw, "MODE EN LIGNE", 100)
                draw_text_centered(surface_to_draw, "IP du Host (Rejoindre):", 280, size=20)
                self.ip_box.draw(surface_to_draw)
            elif self.state == "MENU_STAGE":
                draw_text_centered(surface_to_draw, "CHOIX DU STAGE", 80)
                self.draw_stage_preview(surface_to_draw, self.hovered_stage_idx)
            elif self.state == "MENU_CHAR":
                draw_text_centered(surface_to_draw, "CHOIX DU COMBATTANT", 80)
                # Afficher la preview à GAUCHE (logique future : P1 = gauche, P2 = droite)
                self.draw_character_preview(surface_to_draw, self.hovered_char_idx, side="left")
            elif self.state == "RULES":
                draw_text_centered(surface_to_draw, "RÈGLES", 80)
                rules_lines = ["Q/D: Bouger", "ESPACE: Sauter", "Host lance en premier"]
                for i, line in enumerate(rules_lines):
                    draw_text_centered(surface_to_draw, line, 180 + i * 40, size=24)

            if not self.popup_error:
                # Dessiner les boutons avec gestion du scroll pour les stages
                if self.state == "MENU_STAGE":
                    # Créer une surface de clipping pour les stages
                    clip_rect = pygame.Rect(self.stage_start_x - 10, self.stage_start_y - 10, 
                                           self.stage_columns * (self.stage_button_width + self.stage_padding) + 20,
                                           self.height - self.stage_start_y - 110)
                    
                    # Sauvegarder l'état de clipping actuel
                    original_clip = surface_to_draw.get_clip()
                    surface_to_draw.set_clip(clip_rect)
                    
                    # Dessiner les boutons de stages avec offset
                    for btn in self.stage_buttons:
                        # Créer une copie temporaire du rect avec l'offset
                        original_y = btn.rect.y
                        btn.rect.y += self.stage_scroll_offset
                        
                        # Dessiner seulement si visible
                        if btn.rect.y + btn.rect.height > self.stage_start_y - 10 and btn.rect.y < clip_rect.bottom:
                            btn.draw(surface_to_draw)
                        
                        # Restaurer la position originale
                        btn.rect.y = original_y
                    
                    # Restaurer le clipping
                    surface_to_draw.set_clip(original_clip)
                    
                    # Dessiner le bouton retour (pas affecté par le scroll)
                    self.btn_stage_back.draw(surface_to_draw)
                    
                    # Indicateur de scroll si nécessaire
                    num_rows = (len(self.available_stages) + self.stage_columns - 1) // self.stage_columns
                    total_height = num_rows * (self.stage_button_height + self.stage_padding)
                    visible_height = self.height - self.stage_start_y - 120
                    if total_height > visible_height:
                        # Barre de scroll visuelle
                        scrollbar_x = clip_rect.right + 10
                        scrollbar_height = clip_rect.height
                        scrollbar_y = clip_rect.top
                        
                        # Fond de la scrollbar
                        pygame.draw.rect(surface_to_draw, (50, 50, 50), 
                                       (scrollbar_x, scrollbar_y, 10, scrollbar_height), border_radius=5)
                        
                        # Curseur de la scrollbar
                        scroll_ratio = abs(self.stage_scroll_offset) / (total_height - visible_height)
                        cursor_height = max(30, scrollbar_height * (visible_height / total_height))
                        cursor_y = scrollbar_y + scroll_ratio * (scrollbar_height - cursor_height)
                        pygame.draw.rect(surface_to_draw, (150, 150, 150), 
                                       (scrollbar_x, cursor_y, 10, cursor_height), border_radius=5)
                else:
                    # Dessiner normalement les autres boutons
                    for btn in active_buttons:
                        btn.draw(surface_to_draw)

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
                msg_rect = msg_surf.get_rect(center=(self.width // 2, 290))
                surface_to_draw.blit(msg_surf, msg_rect)

                self.btn_popup_ok.draw(surface_to_draw)

            # SCALING MANUEL
            render_engine.screen.fill((0, 0, 0))
            target_w = int(render_engine.logical_width * render_engine.scale)
            target_h = int(render_engine.logical_height * render_engine.scale)
            scaled = pygame.transform.scale(surface_to_draw, (target_w, target_h))
            render_engine.screen.blit(scaled, (render_engine.offset_x, render_engine.offset_y))

            pygame.display.flip()
            self.clock.tick(60)