import sys
import pygame
from src.CoreEngine.EngineRender import EngineRender
from src.CoreEngine.EngineTick import EngineTick
from src.CoreEngine.Menus import MenuSystem
from src.Entities.Player import Player
from src.Entities.Platform import Platform
from src.Network.NetworkManager import NetworkManager

WIDTH, HEIGHT = 800, 600


def get_local_inputs():
    k = pygame.key.get_pressed()
    return {"left": k[pygame.K_q], "right": k[pygame.K_d], "jump": k[pygame.K_SPACE]}


def draw_centered_text(render_engine, text, y, size=30, color=(255, 255, 255)):
    # helper pr centrer le txt ez
    font = pygame.font.SysFont("Arial", size, bold=True)
    surf = font.render(text, True, color)
    rect = surf.get_rect(center=(WIDTH // 2, y))
    render_engine.screen.blit(surf, rect)


def run_game(mode, ip_target="localhost"):
    title = f"RiftFighters - {mode}"
    render = EngineRender(WIDTH, HEIGHT, title=title)
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

        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: return
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: return

            # check connection
            network.accept_client(server_socket)
            if network.connected: waiting = False

            # render ui d'attente
            render.screen.fill((20, 20, 40))

            draw_centered_text(render, "EN ATTENTE D'UN JOUEUR...", 50, size=40, color=(255, 200, 50))

            # bloc 1 : lan (meme wifi)
            pygame.draw.rect(render.screen, (50, 50, 100), (100, 120, 600, 150), border_radius=10)
            draw_centered_text(render, "OPTION A : lan (meme wifi)", 140, size=22, color=(150, 200, 255))
            draw_centered_text(render, "ip locale a donner :", 180, size=18)
            draw_centered_text(render, f"{network.local_ip}", 220, size=50, color=(100, 255, 100))

            # bloc 2 : wan (internet)
            pygame.draw.rect(render.screen, (100, 50, 50), (100, 300, 600, 150), border_radius=10)
            draw_centered_text(render, "OPTION B : wan (internet)", 320, size=22, color=(255, 150, 150))
            draw_centered_text(render, "ip publique (box) a donner :", 360, size=18)
            draw_centered_text(render, f"{network.public_ip}", 400, size=50, color=(255, 100, 100))

            draw_centered_text(render, "(echap pr annuler)", 550, size=20, color=(100, 100, 100))

            pygame.display.flip()
            clock.tick(30)

    # --- game loop ---
    # spawn actors
    ground = Platform(0, 500, 800, 100)
    p1 = Player(100, 300, color=(0, 255, 0))
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
        # a. events
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: running = False

        my_inputs = get_local_inputs()

        # b. logic + net
        if mode == "SOLO":
            p1.update_inputs(my_inputs)
            tick_engine.update_tick()

        elif mode == "HOST":
            if network.connected:
                client_data = network.receive()
                if client_data: p2.update_inputs(client_data)

                # server authority sur p1 et p2
                p1.update_inputs(my_inputs)
                tick_engine.update_tick()

                # rep state world au client
                network.send({"p1": (p1.x, p1.y), "p2": (p2.x, p2.y)})

        elif mode == "CLIENT":
            p2.update_inputs(my_inputs)
            tick_engine.update_tick()  # client prediction
            network.send(my_inputs)

            # sync avec server
            server_state = network.receive()
            if server_state:
                p1.x, p1.y = server_state["p1"]
                p2.reconcile(*server_state["p2"])

        # c. render
        render.render_frame()


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("RiftFighters - Menu")
    menu_system = MenuSystem(WIDTH, HEIGHT)

    while True:
        # update menu
        result = menu_system.run(screen)
        if result['action'] == 'QUIT':
            break
        elif result['action'] == 'GAME':
            # launch game context
            run_game(result['mode'], result.get('ip', 'localhost'))

            # reset display apres game
            screen = pygame.display.set_mode((WIDTH, HEIGHT))
            pygame.display.set_caption("RiftFighters - Menu")

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()