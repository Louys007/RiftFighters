import sys
import pygame
import os
from src.CoreEngine.EngineRender import EngineRender
from src.CoreEngine.EngineTick import EngineTick
# Import de la fonction draw_text_centered depuis Menus
from src.CoreEngine.Menus import MenuSystem, Button, draw_text_centered
from src.Entities.Player import CubeFighter, RedStriker
from src.Entities.Platform import Platform
from src.Network.NetworkManager import NetworkManager

WIDTH, HEIGHT = 800, 600


def get_local_inputs():
    k = pygame.key.get_pressed()
    return {"left": k[pygame.K_q], "right": k[pygame.K_d], "jump": k[pygame.K_SPACE]}


def run_game(mode, ip_target, stage_file, player_class):
    title = f"RiftFighters - {mode}"
    bg_path = os.path.join("assets", "Stages", stage_file)

    # Init Moteur
    try:
        render = EngineRender(WIDTH, HEIGHT, title=title, background_image=bg_path)
        tick_engine = EngineTick()
    except Exception as e:
        return f"Erreur Init Moteur: {e}"

    network = None
    server_socket = None

    # --- 1. NETWORK INIT ---
    if mode == "HOST":
        try:
            network = NetworkManager()
            server_socket = network.host_game()
        except Exception as e:
            return f"Erreur Création Host: {e}"
    elif mode == "CLIENT":
        try:
            network = NetworkManager()
            network.join_game(ip_target)
            if not network.connected:
                return f"Échec connexion vers {ip_target}"
        except Exception as e:
            return f"Erreur Connexion: {e}"

    # --- 2. LOBBY (HOST ONLY) ---
    if mode == "HOST":
        waiting = True
        clock = pygame.time.Clock()
        btn_firewall = Button(250, 480, 300, 40, "ouvrir pare-feu (admin)", "FIX_FW", color=(200, 50, 50))
        firewall_ok = network.check_firewall_rule()
        last_check_timer = pygame.time.get_ticks()

        while waiting:
            # Fond sombre
            render.screen.blit(render.background, (0, 0))
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(150)
            overlay.fill((0, 0, 0))
            render.screen.blit(overlay, (0, 0))

            mouse_pos = pygame.mouse.get_pos()

            # Check Firewall
            if pygame.time.get_ticks() - last_check_timer > 2000:
                firewall_ok = network.check_firewall_rule()
                last_check_timer = pygame.time.get_ticks()

            for event in pygame.event.get():
                if event.type == pygame.QUIT: return "Host a quitté le lobby"
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: return "Annulé par l'utilisateur"

                if not firewall_ok and btn_firewall.handle_event(event) == "FIX_FW":
                    network.open_firewall()

            # Check Client
            network.accept_client(server_socket)
            if network.connected: waiting = False

            # Affichage Lobby (utilise draw_text_centered importé)
            draw_text_centered(render.screen, "SALLE D'ATTENTE", 50, size=50, color=(255, 200, 50))
            draw_text_centered(render.screen, f"Stage: {stage_file} | Perso: {player_class.CLASS_NAME}", 90, size=20,
                               color=(200, 200, 200))

            # Bloc LAN
            pygame.draw.rect(render.screen, (50, 50, 100), (100, 130, 600, 100), border_radius=10)
            draw_text_centered(render.screen, "LAN (Wifi maison) - IP Locale :", 155, size=20, color=(150, 200, 255))
            draw_text_centered(render.screen, f"{network.local_ip}", 190, size=35, color=(100, 255, 100))

            # Bloc WAN
            color_frame = (100, 50, 50) if not firewall_ok else (50, 100, 50)
            pygame.draw.rect(render.screen, color_frame, (100, 250, 600, 150), border_radius=10)
            draw_text_centered(render.screen, "INTERNET (IP Publique) :", 270, size=20, color=(255, 150, 150))
            draw_text_centered(render.screen, f"{network.public_ip}", 310, size=35, color=(255, 100, 100))
            draw_text_centered(render.screen, "(Donnez cette IP à votre ami)", 350, size=18)

            if not firewall_ok:
                draw_text_centered(render.screen, "⚠️ Pare-feu bloquant !", 450, size=20, color=(255, 255, 0))
                btn_firewall.check_hover(mouse_pos)
                btn_firewall.draw(render.screen)
            else:
                draw_text_centered(render.screen, "✅ Pare-feu configuré", 450, size=20, color=(100, 255, 100))

            draw_text_centered(render.screen, "En attente d'un adversaire...", 550, size=24)

            pygame.display.flip()
            clock.tick(30)

    # --- 3. GAME LOOP ---
    ground = Platform(0, 500, 800, 100)
    p1 = player_class(96, 300)
    p2 = None

    render.add_object(ground)
    render.add_object(p1)
    tick_engine.add_obstacle(ground)
    tick_engine.add_entity(p1)

    if mode != "SOLO":
        # Placeholder P2
        p2 = CubeFighter(600, 300, color=(100, 100, 200))
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
            if network and network.connected:
                try:
                    client_data = network.receive()
                    if client_data and p2: p2.update_inputs(client_data)
                    p1.update_inputs(my_inputs)
                    tick_engine.update_tick()
                    if p2: network.send({"p1": (p1.x, p1.y), "p2": (p2.x, p2.y)})
                except:
                    return "Erreur communication Client"

        elif mode == "CLIENT":
            if p2: p2.update_inputs(my_inputs)
            tick_engine.update_tick()
            if network:
                try:
                    network.send(my_inputs)
                    server_state = network.receive()
                    if server_state:
                        p1.x, p1.y = server_state["p1"]
                        if p2: p2.reconcile(*server_state["p2"])
                except:
                    return "Déconnexion du Serveur"

        render.render_frame()

    return None


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
            error_msg = run_game(
                mode=result['mode'],
                ip_target=result.get('ip', 'localhost'),
                stage_file=result['stage'],
                player_class=result['character_class']
            )

            # Reset écran après le jeu
            screen = pygame.display.set_mode((WIDTH, HEIGHT))
            pygame.display.set_caption("RiftFighters - Menu")

            # Si erreur retournée, on l'affiche
            if error_msg:
                menu_system.show_error(error_msg)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()