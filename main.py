import sys
import pygame
import os
from src.CoreEngine.EngineRender import EngineRender
from src.CoreEngine.EngineTick import EngineTick
from src.CoreEngine.Menus import MenuSystem, Button, draw_text_centered
from src.CoreEngine.GameUI import GameUI
from src.Entities.Player import *
from src.Entities.Platform import Platform
from src.Network.NetworkManager import NetworkManager

# --- CHANGEMENT RESOLUTION INTERNE ---
WIDTH, HEIGHT = 1280, 720

# --- CONFIGURATION DES PERSOS ---
CHARACTERS_DATA = {
    "Cromagnon": {
        "name": "Cromagnon",
        "image": "cromagnon/cromagnon_idle.png",
        "size": (180, 270),
        "speed": 14,
        "jump": -28,
        "gravity": 2,
        "hitbox_width_ratio": 0.45,
        "hitbox_height_ratio": 0.85
    },
    "Robot": {
        "name": "Robot",
        "image": "robot/robot_idle.png",
        "size": (240, 240),
        "speed": 10,
        "jump": -35,
        "gravity": 2,
        "hitbox_width_ratio": 0.45,
        "hitbox_height_ratio": 0.85
    },
    "Samourai": {
        "name": "Samourai",
        "image": "samourai/samourai_idle.png",
        "size": (200, 280),
        "speed": 16,
        "jump": -32,
        "gravity": 2,
        "hitbox_width_ratio": 0.45,
        "hitbox_height_ratio": 0.85
    }
}


def get_local_inputs_p1():
    k = pygame.key.get_pressed()
    return {"left": k[pygame.K_q], "right": k[pygame.K_d], "jump": k[pygame.K_SPACE], "attack": k[pygame.K_g],
            "shield": k[pygame.K_n]}


def get_local_inputs_p2():
    k = pygame.key.get_pressed()
    return {"left": k[pygame.K_LEFT], "right": k[pygame.K_RIGHT], "jump": k[pygame.K_UP], "attack": k[pygame.K_RETURN],
            "shield": k[pygame.K_m]}


def run_game(mode, ip_target, stage_file, player_name, start_size, solo_mode="1v0", player2_name=None):
    title = f"RiftFighters - {mode}"
    bg_path = os.path.join("assets", "Stages", stage_file)

    try:
        render = EngineRender(WIDTH, HEIGHT, title=title, background_image=bg_path, window_size=start_size)
        tick_engine = EngineTick()
        game_ui = GameUI(WIDTH, HEIGHT, match_duration=180)
    except Exception as e:
        return f"Erreur Init Moteur: {e}", start_size

    network = None
    server_socket = None
    opponent_character = None

    if mode == "HOST":
        try:
            network = NetworkManager()
            server_socket = network.host_game()
        except Exception as e:
            return f"Erreur Création Host: {e}", render.screen.get_size()
    elif mode == "CLIENT":
        try:
            network = NetworkManager()
            # On envoie notre player_name et on récupère celui du Host
            opponent_character = network.join_game(ip_target, player_name)
            if not network.connected:
                return f"Échec connexion vers {ip_target}", render.screen.get_size()
        except Exception as e:
            return f"Erreur Connexion: {e}", render.screen.get_size()

    # --- LOBBY (HOST ONLY) ---
    if mode == "HOST":
        waiting = True
        clock = pygame.time.Clock()
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

            client_char = network.accept_client(server_socket, player_name)
            if network.connected:
                opponent_character = client_char
                waiting = False

            draw_text_centered(render.internal_surface, "SALLE D'ATTENTE", 50, size=50, color=(255, 200, 50))
            draw_text_centered(render.internal_surface, f"Stage: {stage_file} | Perso: {player_name}", 90, size=20,
                               color=(200, 200, 200))

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
    ground = Platform(0, 620, 1280, 100)

    # 1. Détermination des noms des personnages selon le rôle
    p1_name = player_name
    p2_name = None

    if mode == "HOST":
        p1_name = player_name  # L'hôte joue p1
        p2_name = opponent_character if opponent_character else "Cromagnon"
    elif mode == "CLIENT":
        p1_name = opponent_character if opponent_character else "Cromagnon"  # L'hôte (p1) est l'adversaire
        p2_name = player_name  # Le client joue p2
    elif mode == "SOLO":
        p1_name = player_name
        if solo_mode == "1v1":
            p2_name = player2_name if player2_name else "Robot"

    # 2. Création du joueur 1 (Toujours le Host/Joueur Local 1)
    p1_config = CHARACTERS_DATA.get(p1_name, CHARACTERS_DATA["Cromagnon"])
    p1 = Player(96, 400, config=p1_config)
    render.add_object(ground)
    render.add_object(p1)
    tick_engine.add_obstacle(ground)
    tick_engine.add_entity(p1)

    # 3. Création du joueur 2 (Toujours le Client/Joueur 2)
    p2 = None
    if p2_name:
        p2_config = CHARACTERS_DATA.get(p2_name, CHARACTERS_DATA["Cromagnon"])
        p2 = Player(1080, 400, config=p2_config)
        render.add_object(p2)
        tick_engine.add_entity(p2)

        # --- LIAISON POUR LE REGARD AUTOMATIQUE ---
        p1.set_opponent(p2)
        p2.set_opponent(p1)

    # Démarrage du match
    game_ui.set_players(p1, p2, show_controls=(mode == "SOLO" and solo_mode == "1v1"))
    game_ui.start_match()
    render.set_hud(game_ui)
    render.set_tick_engine(tick_engine)

    running = True
    game_over = False

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.VIDEORESIZE:
                render.update_scale_factors()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        if not game_over:
            my_inputs_p1 = get_local_inputs_p1()
            my_inputs_p2 = get_local_inputs_p2() if p2 and mode == "SOLO" else None

            if mode == "SOLO":
                p1.update_inputs(my_inputs_p1)
                if p2 and my_inputs_p2:
                    p2.update_inputs(my_inputs_p2)
                tick_engine.update_tick()


            elif mode == "HOST":

                if network and network.connected:

                    try:

                        packet = network.receive()

                        client_seq = 0

                        if packet and p2:
                            client_data = packet["data"]

                            client_seq = packet["seq"]

                            p2.update_inputs(client_data)

                        p1.update_inputs(my_inputs_p1)

                        tick_engine.update_tick()

                        if p2:
                            # --- ENVOI DE L'ÉTAT COMPLET ET DES TOUCHES AU CLIENT ---

                            network.send({

                                "p1_inputs": my_inputs_p1,  # <-- L'Hôte transmet ses touches

                                "p1": {

                                    "x": p1.x, "y": p1.y, "hp": p1.health,

                                    "facing_right": p1.facing_right,

                                    "is_moving": p1.is_moving,

                                    "on_ground": p1.on_ground,

                                    "shielding": p1.shielding,

                                    "shield_cooldown": p1.shield_cooldown,

                                    "is_dashing": p1.is_dashing,

                                    "dash_cooldown": p1.dash_cooldown,

                                    "attack_phase": p1.attack_phase,

                                    "attack_frame": p1.attack_frame,

                                    "is_alive": p1.is_alive

                                },

                                "p2": {

                                    "x": p2.x, "y": p2.y, "hp": p2.health,

                                    "shield_cooldown": p2.shield_cooldown,

                                    "dash_cooldown": p2.dash_cooldown

                                }

                            }, ack_seq=client_seq)

                    except Exception as e:

                        print(f"Erreur boucle HOST: {e}")


            elif mode == "CLIENT":

                if network:

                    try:

                        my_seq = network.local_seq + 1

                        if p2:
                            # --- CORRECTION : Le Client applique ses propres touches à son perso ---

                            p2.update_inputs(my_inputs_p1)

                            p2.predict_movement(my_seq, my_inputs_p1)

                        tick_engine.update_tick()

                        network.send(my_inputs_p1)

                        packet = network.receive()

                        if packet:

                            server_state = packet["data"]

                            server_ack = packet["ack_seq"]

                            # --- CORRECTION : On simule les touches du Host sur P1 ---

                            # Cela empêche le tick local du client d'annuler le bouclier ou l'attaque de l'Hôte

                            p1.update_inputs(server_state.get("p1_inputs", {}))

                            p1_state = server_state["p1"]

                            p1.x = p1_state["x"]

                            p1.y = p1_state["y"]

                            p1.health = p1_state["hp"]

                            p1.facing_right = p1_state["facing_right"]

                            p1.is_moving = p1_state["is_moving"]

                            p1.on_ground = p1_state["on_ground"]

                            p1.shielding = p1_state["shielding"]

                            p1.shield_cooldown = p1_state["shield_cooldown"]

                            p1.is_dashing = p1_state["is_dashing"]

                            p1.dash_cooldown = p1_state["dash_cooldown"]

                            p1.attack_phase = p1_state["attack_phase"]

                            p1.attack_frame = p1_state["attack_frame"]

                            p1.is_alive = p1_state["is_alive"]

                            if p2:
                                p2_state = server_state["p2"]

                                p2.health = p2_state["hp"]

                                p2.shield_cooldown = p2_state["shield_cooldown"]

                                p2.dash_cooldown = p2_state["dash_cooldown"]

                                p2.reconcile(p2_state["x"], p2_state["y"], server_ack)

                    except Exception as e:

                        print(f"Erreur boucle CLIENT: {e}")

            game_ui.update()

            if game_ui.is_time_up():
                if not p2:
                    game_ui.set_game_over("JOUEUR 1")
                else:
                    if p1.health > p2.health:
                        game_ui.set_game_over("JOUEUR 1")
                    elif p2.health > p1.health:
                        game_ui.set_game_over("JOUEUR 2")
                    else:
                        game_ui.set_game_over(None)
                game_over = True

            if p2:
                if not p1.is_alive and p2.is_alive:
                    game_ui.set_game_over("JOUEUR 2")
                    game_over = True
                elif not p2.is_alive and p1.is_alive:
                    game_ui.set_game_over("JOUEUR 1")
                    game_over = True
                elif not p1.is_alive and not p2.is_alive:
                    game_ui.set_game_over(None)
                    game_over = True

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
                player_name=result['character_class'],
                start_size=current_window_size,
                solo_mode=result.get('solo_mode', '1v0'),
                player2_name=result.get('character_class_p2', None)  # ← nouveau paramètre
            )

            current_window_size = new_size
            menu_render = EngineRender(WIDTH, HEIGHT, title="RiftFighters - Menu", window_size=current_window_size)

            if error_msg:
                menu_system.show_error(error_msg)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()