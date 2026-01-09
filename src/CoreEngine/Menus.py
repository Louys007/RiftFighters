import pygame


def draw_text_centered(surface, text, y, size=40, color=(255, 255, 255)):
    font = pygame.font.SysFont("Arial", size, bold=True)
    txt_surf = font.render(text, True, color)
    rect = txt_surf.get_rect(center=(surface.get_width() // 2, y))
    surface.blit(txt_surf, rect)


class Button:
    def __init__(self, x, y, width, height, text, action_code, color=(50, 150, 255), hover_color=(70, 170, 255),
                 text_color=(255, 255, 255)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action_code = action_code
        self.base_color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.font = pygame.font.SysFont("Arial", 24, bold=True)
        self.is_hovered = False

    def check_hover(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered:
                return self.action_code
        return None

    def draw(self, surface):
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
                    if len(self.text) < 20:
                        self.text += event.unicode
                self.txt_surface = self.font.render(self.text, True, self.color)

    def draw(self, screen):
        screen.blit(self.txt_surface, (self.rect.x + 5, self.rect.y + 5))
        pygame.draw.rect(screen, self.color, self.rect, 2)


class MenuSystem:
    def __init__(self, width, height):
        self.state = "MENU_MAIN"
        self.clock = pygame.time.Clock()

        # Menu Principal
        self.main_buttons = [
            Button(300, 200, 200, 50, "Entraînement", "GO_SOLO"),
            Button(300, 270, 200, 50, "Multijoueur", "GO_MULTI_MENU"),
            Button(300, 340, 200, 50, "Règles", "GO_RULES"),
            Button(300, 450, 200, 50, "Quitter", "QUIT", color=(200, 50, 50), hover_color=(255, 50, 50))
        ]

        # Menu Multi
        self.multi_buttons = [
            Button(300, 200, 200, 50, "Héberger (Host)", "DO_HOST"),
            Button(300, 360, 200, 50, "Rejoindre IP", "DO_JOIN"),
            Button(300, 500, 200, 50, "Retour", "BACK")
        ]
        self.ip_box = InputBox(300, 300, 200, 40, "localhost")

        # Menu Règles
        self.btn_back = Button(300, 500, 200, 50, "Retour", "BACK")

    def run(self, screen):
        """
        Lance la boucle du menu sur l'écran donné.
        """
        running = True
        while running:
            screen.fill((30, 30, 30))
            mouse_pos = pygame.mouse.get_pos()

            # GESTION EVENEMENTS
            action = None
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return {'action': 'QUIT'}

                if self.state == "MENU_MAIN":
                    for btn in self.main_buttons:
                        res = btn.handle_event(event)
                        if res: action = res

                elif self.state == "MENU_MULTI":
                    self.ip_box.handle_event(event)
                    for btn in self.multi_buttons:
                        res = btn.handle_event(event)
                        if res: action = res

                elif self.state == "RULES":
                    if self.btn_back.handle_event(event): action = "BACK"

            # NAVIGATION
            if action:
                if action == "QUIT":
                    return {'action': 'QUIT'}
                elif action == "GO_SOLO":
                    return {'action': 'GAME', 'mode': 'SOLO'}
                elif action == "GO_MULTI_MENU":
                    self.state = "MENU_MULTI"
                elif action == "GO_RULES":
                    self.state = "RULES"
                elif action == "BACK":
                    self.state = "MENU_MAIN"
                elif action == "DO_HOST":
                    return {'action': 'GAME', 'mode': 'HOST'}
                elif action == "DO_JOIN":
                    return {'action': 'GAME', 'mode': 'CLIENT', 'ip': self.ip_box.text}

            # DESSIN
            if self.state == "MENU_MAIN":
                draw_text_centered(screen, "RIFT FIGHTERS", 100, size=60, color=(255, 200, 50))
                for btn in self.main_buttons:
                    btn.check_hover(mouse_pos)
                    btn.draw(screen)

            elif self.state == "MENU_MULTI":
                draw_text_centered(screen, "MODE EN LIGNE", 100)
                draw_text_centered(screen, "IP du Host (pour Rejoindre):", 280, size=20)
                self.ip_box.draw(screen)
                for btn in self.multi_buttons:
                    btn.check_hover(mouse_pos)
                    btn.draw(screen)

            elif self.state == "RULES":
                draw_text_centered(screen, "RÈGLES DU JEU", 80)
                rules_lines = [
                    "Déplacez-vous avec Q et D",
                    "Sautez avec ESPACE",
                    "Le mode Multijoueur nécessite",
                    "que le HOST lance en premier.",
                    "Entrez l'IP du Host pour rejoindre."
                ]
                for i, line in enumerate(rules_lines):
                    draw_text_centered(screen, line, 180 + i * 40, size=24)

                self.btn_back.check_hover(mouse_pos)
                self.btn_back.draw(screen)

            pygame.display.flip()
            self.clock.tick(60)