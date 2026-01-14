from statistics import mode
import sys
import pygame
import os
from src.CoreEngine.EngineRender import EngineRender
from src.CoreEngine.EngineTick import EngineTick
from src.CoreEngine.Menus import MenuSystem, Button, draw_text_centered
from src.Entities.Player import *
from src.Entities.Platform import Platform
from src.Network.NetworkManager import NetworkManager

# --- CHANGEMENT RESOLUTION INTERNE ---
WIDTH, HEIGHT = 1280, 720

# --- CONFIGURATION DES PERSOS ---
CHARACTERS_DATA = {
    "Cromagnon": {
        "name": "Cromagnon",
        "image": "cromagnon.png", # Doit être dans assets/Perso/
        "size": (180, 270),
        "speed": 14,
        "jump": -28,
        "gravity": 2
    },
    "Robot": {
        "name": "Robot",
        "image": "robot.png",     # Doit être dans assets/Perso/
        "size": (240, 240),
        "speed": 10,       # Plus lent
        "jump": -35,       # Saute plus haut
        "gravity": 2
    }
}

def get_local_inputs():
    k = pygame.key.get_pressed()
    return {"left": k[pygame.K_q], "right": k[pygame.K_d], "jump": k[pygame.K_SPACE]}


def run_game(mode, ip_target, stage_file, player_name, start_size):
    title = f"RiftFighters - {mode}"
    bg_path = os.path.join("assets", "Stages", stage_file)

    try:
        render = EngineRender(WIDTH, HEIGHT, title=title, background_image=bg_path, window_size=start_size)
        tick_engine = EngineTick()
    except Exception as e:
        return f"Erreur Init Moteur: {e}", start_size

    network = None
    server_socket = None

    if mode == "HOST":
        try:
            network = NetworkManager()
            server_socket = network.host_game()
        except Exception as e:
            return f"Erreur Création Host: {e}", render.screen.get_size()
    elif mode == "CLIENT":
        try:
            network = NetworkManager()
            network.join_game(ip_target)
            if not network.connected:
                return f"Échec connexion vers {ip_target}", render.screen.get_size()
        except Exception as e:
            return f"Erreur Connexion: {e}", render.screen.get_size()

    # --- LOBBY (HOST ONLY) ---
    if mode == "HOST":
        waiting = True
        clock = pygame.time.Clock()
        # Bouton centré
        btn_firewall = Button(WIDTH // 2 - 150, 480, 300, 40, "ouvrir pare-feu (admin)", "FIX_FW", color=(200, 50, 50))
        firewall_ok = network.check_firewall_rule()
        last_check_timer = pygame.time.get_ticks()

        while waiting:
            render.internal_surface.blit(render.background, (0, 0))
            overlay = pygame.Surface((WIDTH, HEIGHT))
            overlay.set_alpha(150)
            overlay.fill((0, 0, 0))
            render.internal_surface.blit(overlay, (0, 0))

            mouse_pos = render.get_virtual_mouse_pos()

            if pygame.time.get_ticks() - last_check_timer > 2000:
                firewall_ok = network.check_firewall_rule()
                last_check_timer = pygame.time.get_ticks()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return "Host a quitté le lobby", render.screen.get_size()
                if event.type == pygame.VIDEORESIZE:
                    render.update_scale_factors()
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    return "Annulé par l'utilisateur", render.screen.get_size()

                btn_firewall.check_hover(mouse_pos)
                if not firewall_ok and event.type == pygame.MOUSEBUTTONDOWN:
                    if btn_firewall.is_hovered:
                        network.open_firewall()

            network.accept_client(server_socket)
            if network.connected: waiting = False

            draw_text_centered(render.internal_surface, "SALLE D'ATTENTE", 50, size=50, color=(255, 200, 50))
            draw_text_centered(render.internal_surface, f"Stage: {stage_file} | Perso: {player_name}", 90,
                               size=20, color=(200, 200, 200))

            # Cadres centrés
            cx = WIDTH // 2
            pygame.draw.rect(render.internal_surface, (50, 50, 100), (cx - 300, 130, 600, 100), border_radius=10)
            draw_text_centered(render.internal_surface, "LAN (Wifi maison) - IP Locale :", 155, size=20,
                               color=(150, 200, 255))
            draw_text_centered(render.internal_surface, f"{network.local_ip}", 190, size=35, color=(100, 255, 100))

            color_frame = (100, 50, 50) if not firewall_ok else (50, 100, 50)
            pygame.draw.rect(render.internal_surface, color_frame, (cx - 300, 250, 600, 150), border_radius=10)
            draw_text_centered(render.internal_surface, "INTERNET (IP Publique) :", 270, size=20, color=(255, 150, 150))
            draw_text_centered(render.internal_surface, f"{network.public_ip}", 310, size=35, color=(255, 100, 100))
            draw_text_centered(render.internal_surface, "(Donnez cette IP à votre ami)", 350, size=18)

            if not firewall_ok:
                draw_text_centered(render.internal_surface, "⚠️ Pare-feu bloquant !", 450, size=20, color=(255, 255, 0))
                btn_firewall.check_hover(mouse_pos)
                btn_firewall.draw(render.internal_surface)
            else:
                draw_text_centered(render.internal_surface, "✅ Pare-feu configuré", 450, size=20, color=(100, 255, 100))

            draw_text_centered(render.internal_surface, "En attente d'un adversaire...", 550, size=24)

            render.screen.fill((0, 0, 0))
            scaled = pygame.transform.scale(render.internal_surface,
                                            (int(WIDTH * render.scale), int(HEIGHT * render.scale)))
            render.screen.blit(scaled, (render.offset_x, render.offset_y))
            pygame.display.flip()
            clock.tick(30)

    # --- GAME LOOP ---
    # AJUSTEMENT POSITIONS : Sol en bas (720-100 = 620), Largeur 1280
    ground = Platform(0, 620, 1280, 100)

    p1_config = CHARACTERS_DATA.get(player_name, CHARACTERS_DATA["Cromagnon"]) # Fallback sur Cro-magnon
    p1 = Player(96, 400, config=p1_config)
    p2 = None

    render.add_object(ground)
    render.add_object(p1)
    tick_engine.add_obstacle(ground)
    tick_engine.add_entity(p1)

    if mode != "SOLO":
        # Pour le joueur 2, disons qu'il prend l'autre perso par défaut pour le test
        # (Ou tu peux recevoir le choix du P2 via le réseau plus tard)
        p2_name = "Robot" if player_name == "Cromagnon" else "Cromagnon"
        p2_config = CHARACTERS_DATA[p2_name]
        
        p2 = Player(1080, 400, config=p2_config)
        render.add_object(p2)
        tick_engine.add_entity(p2)

    clock = pygame.time.Clock()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False
            if event.type == pygame.VIDEORESIZE:
                render.update_scale_factors()
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
                    return "Erreur communication Client", render.screen.get_size()

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
                    return "Déconnexion du Serveur", render.screen.get_size()

        render.render_frame()

    final_size = render.screen.get_size()
    return None, final_size


def main():
    pygame.init()

    info = pygame.display.Info()
    current_window_size = (info.current_w, info.current_h)

    menu_render = EngineRender(WIDTH, HEIGHT, title="RiftFighters - Menu", window_size=current_window_size)
    menu_system = MenuSystem(WIDTH, HEIGHT)

    while True:
        result = menu_system.run(menu_render)

        if result['action'] == 'QUIT':
            break
        elif result['action'] == 'GAME':
            current_window_size = menu_render.screen.get_size()

            pygame.display.quit()
            pygame.display.init()

            error_msg, new_size = run_game(
                mode=result['mode'],
                ip_target=result.get('ip', 'localhost'),
                stage_file=result['stage'],
                player_name=result['character_class'], # C'est maintenant un String
                start_size=current_window_size
            )

            current_window_size = new_size
            menu_render = EngineRender(WIDTH, HEIGHT, title="RiftFighters - Menu", window_size=current_window_size)

            if error_msg:
                menu_system.show_error(error_msg)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()