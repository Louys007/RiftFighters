import sys
import pygame
import os
from src.CoreEngine.EngineRender import EngineRender
from src.CoreEngine.EngineTick import EngineTick
from src.CoreEngine.Menus import MenuSystem, Button  # <--- Ajout de Button ici
from src.Entities.Player import Player
from src.Entities.Platform import Platform
from src.Network.NetworkManager import NetworkManager

WIDTH, HEIGHT = 800, 600


def get_local_inputs():
    k = pygame.key.get_pressed()
    return {"left": k[pygame.K_q], "right": k[pygame.K_d], "jump": k[pygame.K_SPACE]}


def draw_centered_text(render_engine, text, y, size=30, color=(255, 255, 255)):
    font = pygame.font.SysFont("Arial", size, bold=True)
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(WIDTH // 2, y))
    render_engine.screen.blit(surf, rect)


def run_game(mode, ip_target="localhost"):
    title = f"RiftFighters - {mode}"
    render = EngineRender(WIDTH, HEIGHT, title=title, background_image="assets/stage_labo.png")
    tick_engine = EngineTick()
    network = None
    server_socket = None

    # init net
    if mode == "HOST":
        network = NetworkManager()
        server_socket = network.host_game()
    elif mode == "CLIENT":
        network = NetworkManager()
        network.join_game(ip_target)

    # --- lobby loop (host only) ---
    if mode == "HOST":
        waiting = True
        clock = pygame.time.Clock()

        # setup bouton pare-feu
        btn_firewall = Button(250, 420, 300, 40, "ouvrir pare-feu (admin)", "FIX_FW", color=(200, 50, 50))
        firewall_ok = network.check_firewall_rule()
        last_check_timer = pygame.time.get_ticks()

        while waiting:
            mouse_pos = pygame.mouse.get_pos()

            # check firewall toutes les 2s (evite de spammer le subprocess)
            if pygame.time.get_ticks() - last_check_timer > 2000:
                firewall_ok = network.check_firewall_rule()
                last_check_timer = pygame.time.get_ticks()

            for event in pygame.event.get():
                if event.type == pygame.QUIT: return
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: return

                # interaction bouton pare-feu
                if not firewall_ok:
                    if btn_firewall.handle_event(event) == "FIX_FW":
                        network.open_firewall()

            # check connection
            network.accept_client(server_socket)
            if network.connected: waiting = False

            # render ui
            render.screen.fill((20, 20, 40))
            draw_centered_text(render, "EN ATTENTE D'UN JOUEUR...", 50, size=40, color=(255, 200, 50))

            # bloc 1 : lan
            pygame.draw.rect(render.screen, (50, 50, 100), (100, 110, 600, 130), border_radius=10)
            draw_centered_text(render, "OPTION A : lan (meme wifi)", 125, size=20, color=(150, 200, 255))
            draw_centered_text(render, f"{network.local_ip}", 160, size=40, color=(100, 255, 100))

            # bloc 2 : wan
            # couleur cadre rouge si firewall pas ok, sinon vert foncé
            color_frame = (100, 50, 50) if not firewall_ok else (50, 100, 50)
            pygame.draw.rect(render.screen, color_frame, (100, 260, 600, 220), border_radius=10)

            draw_centered_text(render, "OPTION B : wan (internet)", 280, size=20, color=(255, 150, 150))
            draw_centered_text(render, "ip publique a donner :", 310, size=18)
            draw_centered_text(render, f"{network.public_ip}", 350, size=40, color=(255, 100, 100))

            # affichage conditionnel bouton
            if not firewall_ok:
                draw_centered_text(render, "⚠️ pare-feu mal configuré !", 390, size=18, color=(255, 255, 0))
                btn_firewall.check_hover(mouse_pos)
                btn_firewall.draw(render.screen)
            else:
                draw_centered_text(render, "✅ pare-feu configuré", 410, size=20, color=(100, 255, 100))

            draw_centered_text(render, "(echap pr annuler)", 550, size=20, color=(100, 100, 100))

            pygame.display.flip()
            clock.tick(30)

    # --- game loop ---
    ground = Platform(0, 500, 800, 100)
    p1 = Player(96, 300, color=(0, 255, 0))
    p2 = None

    render.add_object(ground)
    render.add_object(p1)
    tick_engine.add_obstacle(ground)
    tick_engine.add_entity(p1)

    if mode != "SOLO":
        p2 = Player(600, 300, color=(255, 0, 0))
        render.add_object(p2)
        tick_engine.add_entity(p2)

    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: running = False

        my_inputs = get_local_inputs()

        if mode == "SOLO":
            p1.update_inputs(my_inputs)
            tick_engine.update_tick()

        elif mode == "HOST":
            if network.connected:
                client_data = network.receive()
                if client_data: p2.update_inputs(client_data)
                p1.update_inputs(my_inputs)
                tick_engine.update_tick()
                network.send({"p1": (p1.x, p1.y), "p2": (p2.x, p2.y)})

        elif mode == "CLIENT":
            p2.update_inputs(my_inputs)
            tick_engine.update_tick()
            network.send(my_inputs)

            server_state = network.receive()
            if server_state:
                p1.x, p1.y = server_state["p1"]
                p2.reconcile(*server_state["p2"])

        render.render_frame()


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("RiftFighters - Menu")
    menu_system = MenuSystem(WIDTH, HEIGHT)

    while True:
        result = menu_system.run(screen)
        if result['action'] == 'QUIT':
            break
        elif result['action'] == 'GAME':
            run_game(result['mode'], result.get('ip', 'localhost'))
            screen = pygame.display.set_mode((WIDTH, HEIGHT))
            pygame.display.set_caption("RiftFighters - Menu")

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()