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

        self.available_stages = ["stage_labo.png"]
        self.available_chars = [CubeFighter, RedStriker]

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

        # Boutons larges (Stages)
        bw_l = 400
        bx_l = cx - bw_l // 2

        self.stage_buttons = []
        for i, stage in enumerate(self.available_stages):
            img_path = os.path.join("assets", "Stages", stage)
            self.stage_buttons.append(
                Button(bx_l, 150 + i * 160, bw_l, 150, stage, f"SELECT_STAGE_{i}", image_path=img_path)
            )
        self.btn_stage_back = Button(50, height - 100, 150, 50, "Retour", "BACK_TO_MAIN")

        self.char_buttons = []
        for i, char_cls in enumerate(self.available_chars):
            self.char_buttons.append(
                Button(bx_l, 150 + i * 70, bw_l, 60, char_cls.CLASS_NAME, f"SELECT_CHAR_{i}", color=char_cls.MENU_COLOR)
            )
        self.btn_char_back = Button(50, height - 100, 150, 50, "Retour", "BACK_TO_STAGE")
        self.btn_back = Button(bx, 500, bw, 50, "Retour", "BACK")

    def show_error(self, message):
        self.popup_error = message
        self.state = "MENU_MAIN"

    def run(self, render_engine):
        running = True
        surface_to_draw = render_engine.internal_surface

        while running:
            surface_to_draw.fill((30, 30, 30))
            mouse_pos = render_engine.get_virtual_mouse_pos()

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

            action = None
            for event in pygame.event.get():
                if event.type == pygame.QUIT: return {'action': 'QUIT'}

                if event.type == pygame.VIDEORESIZE:
                    render_engine.update_scale_factors()

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
            elif self.state == "MENU_CHAR":
                draw_text_centered(surface_to_draw, "CHOIX DU COMBATTANT", 80)
            elif self.state == "RULES":
                draw_text_centered(surface_to_draw, "RÈGLES", 80)
                rules_lines = ["Q/D: Bouger", "ESPACE: Sauter", "Host lance en premier"]
                for i, line in enumerate(rules_lines):
                    draw_text_centered(surface_to_draw, line, 180 + i * 40, size=24)

            if not self.popup_error:
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