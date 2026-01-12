import pygame
import os
# On importe les classes de persos pour peupler le menu
from ..Entities.Player import CubeFighter, RedStriker


def draw_text_centered(surface, text, y, size=40, color=(255, 255, 255)):
    """Affiche du texte centré horizontalement sur la surface donnée."""
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

        # Chargement de l'image si fournie
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
            # Cadre blanc si survolé
            if self.is_hovered:
                pygame.draw.rect(surface, (255, 255, 255), self.rect, 4, border_radius=8)

            # Texte avec ombre pour lisibilité sur l'image
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

        # --- Gestion Popup Erreur ---
        self.popup_error = None
        self.btn_popup_ok = Button(300, 350, 200, 50, "OK", "CLOSE_POPUP")

        # --- Données de sélection ---
        self.selected_mode = None
        self.selected_ip = "localhost"
        self.selected_stage = "stage_labo.png"
        self.selected_char_class = CubeFighter

        # --- Contenu (Stages & Persos) ---
        self.available_stages = ["stage_labo.png"]
        self.available_chars = [CubeFighter, RedStriker]

        # --- Menu Principal ---
        self.main_buttons = [
            Button(300, 200, 200, 50, "Entraînement", "PRE_SOLO"),
            Button(300, 270, 200, 50, "Multijoueur", "GO_MULTI_MENU"),
            Button(300, 340, 200, 50, "Règles", "GO_RULES"),
            Button(300, 450, 200, 50, "Quitter", "QUIT", color=(200, 50, 50), hover_color=(255, 50, 50))
        ]

        # --- Menu Multi ---
        self.multi_buttons = [
            Button(300, 200, 200, 50, "Héberger (Host)", "PRE_HOST"),
            Button(300, 360, 200, 50, "Rejoindre IP", "PRE_JOIN"),
            Button(300, 500, 200, 50, "Retour", "BACK")
        ]
        self.ip_box = InputBox(300, 300, 200, 40, "localhost")

        # --- Menu Stage Select ---
        self.stage_buttons = []
        for i, stage in enumerate(self.available_stages):
            img_path = os.path.join("assets", "Stages", stage)
            self.stage_buttons.append(
                Button(200, 150 + i * 160, 400, 150, stage, f"SELECT_STAGE_{i}", image_path=img_path)
            )
        self.btn_stage_back = Button(50, 500, 150, 50, "Retour", "BACK_TO_MAIN")

        # --- Menu Character Select ---
        self.char_buttons = []
        for i, char_cls in enumerate(self.available_chars):
            self.char_buttons.append(
                Button(200, 150 + i * 70, 400, 60, char_cls.CLASS_NAME, f"SELECT_CHAR_{i}", color=char_cls.MENU_COLOR)
            )
        self.btn_char_back = Button(50, 500, 150, 50, "Retour", "BACK_TO_STAGE")

        # --- Menu Règles ---
        self.btn_back = Button(300, 500, 200, 50, "Retour", "BACK")

    def show_error(self, message):
        """Active l'affichage de la popup"""
        self.popup_error = message
        self.state = "MENU_MAIN"

    def run(self, screen):
        running = True
        while running:
            screen.fill((30, 30, 30))
            mouse_pos = pygame.mouse.get_pos()

            # DETERMINER LES BOUTONS ACTIFS
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

            # GESTION EVENEMENTS
            action = None
            for event in pygame.event.get():
                if event.type == pygame.QUIT: return {'action': 'QUIT'}

                # Input box seulement si Multi et pas de popup
                if self.state == "MENU_MULTI" and not self.popup_error:
                    self.ip_box.handle_event(event)

                for btn in active_buttons:
                    res = btn.handle_event(event)
                    if res: action = res

            # LOGIQUE NAVIGATION
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

            # RENDER
            if self.state == "MENU_MAIN":
                draw_text_centered(screen, "RIFT FIGHTERS", 100, size=60, color=(255, 200, 50))
            elif self.state == "MENU_MULTI":
                draw_text_centered(screen, "MODE EN LIGNE", 100)
                draw_text_centered(screen, "IP du Host (Rejoindre):", 280, size=20)
                self.ip_box.draw(screen)
            elif self.state == "MENU_STAGE":
                draw_text_centered(screen, "CHOIX DU STAGE", 80)
            elif self.state == "MENU_CHAR":
                draw_text_centered(screen, "CHOIX DU COMBATTANT", 80)
            elif self.state == "RULES":
                draw_text_centered(screen, "RÈGLES", 80)
                rules_lines = ["Q/D: Bouger", "ESPACE: Sauter", "Host lance en premier"]
                for i, line in enumerate(rules_lines):
                    draw_text_centered(screen, line, 180 + i * 40, size=24)

            # Dessin boutons
            if not self.popup_error:
                for btn in active_buttons:
                    btn.check_hover(mouse_pos)
                    btn.draw(screen)

            # --- DESSIN POPUP ---
            if self.popup_error:
                overlay = pygame.Surface((self.width, self.height))
                overlay.set_alpha(200)
                overlay.fill((0, 0, 0))
                screen.blit(overlay, (0, 0))

                rect_popup = pygame.Rect(150, 200, 500, 250)
                pygame.draw.rect(screen, (50, 0, 0), rect_popup, border_radius=12)
                pygame.draw.rect(screen, (255, 50, 50), rect_popup, 3, border_radius=12)

                draw_text_centered(screen, "ERREUR", 230, size=40, color=(255, 100, 100))

                # Message d'erreur
                msg_surf = pygame.font.SysFont("Arial", 20).render(str(self.popup_error), True, (255, 255, 255))
                msg_rect = msg_surf.get_rect(center=(self.width // 2, 290))
                screen.blit(msg_surf, msg_rect)

                self.btn_popup_ok.check_hover(mouse_pos)
                self.btn_popup_ok.draw(screen)

            pygame.display.flip()
            self.clock.tick(60)