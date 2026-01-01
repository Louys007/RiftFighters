import sys
import pygame
from src.CoreEngine.EngineRender import EngineRender
from src.CoreEngine.EngineTick import EngineTick
from src.Entities.Player import Player
from src.Entities.Platform import Platform
from src.Network.NetworkManager import NetworkManager


def get_local_inputs():
    k = pygame.key.get_pressed()
    return {"left": k[pygame.K_q], "right": k[pygame.K_d], "jump": k[pygame.K_SPACE]}


def main():
    ############### --- SETUP --- ##########################
    pygame.init()
    print("--- RIFT FIGHTERS : CLIENT PREDICTION ---")
    role = input("Héberger (h) ou Rejoindre (j) ? : ").lower()

    network = NetworkManager()
    my_role = None
    server_socket = None  # pour l'host

    if role == "h":
        server_socket = network.host_game()
        if server_socket: my_role = "HOST"
    else:
        ip = input("IP Host : ")
        my_role = network.join_game(ip)

    # on init le moteur
    render = EngineRender(800, 600, title=f"RiftFighters - {my_role}")
    tick_engine = EngineTick()

    # on créé les objets
    ground = Platform(0, 500, 800, 100)
    p1 = Player(100, 300, color=(0, 255, 0))  # Host (Vert)
    p2 = Player(600, 300, color=(255, 0, 0))  # Client (Rouge)

    # on ajoute tous les objets au Render qui va pouvoir ainsi les afficher
    render.add_object(ground)
    render.add_object(p1)
    render.add_object(p2)

    # On ajoute des collisions simples pour l'exemple
    tick_engine.add_obstacle(ground)
    tick_engine.add_entity(p1)
    tick_engine.add_entity(p2)

    clock = pygame.time.Clock()
    running = True

    while running:
        # GESTION CONNEXION (HOST) ----------------------------------------
        if my_role == "HOST" and not network.connected:
            network.accept_client(server_socket)  # Tente d'accepter sans bloquer

        # INPUTS LOCAUX --------------------------------------------------
        for event in pygame.event.get():
            if event.type == pygame.QUIT: running = False

        my_inputs = get_local_inputs()

        # RESEAU + LOGIQUE

        if my_role == "HOST":
            # le host uniquement
            if network.connected:

                # reception des inputs du client (si possible)
                client_data = network.receive()
                if client_data:
                    p2.update_inputs(client_data)

                # met a jour mes propres inputs
                p1.update_inputs(my_inputs)

                # TICK
                # le Host calcule la vérité pour P1 ET P2
                tick_engine.update_tick()

                # On envoie les vraies positions au client ( on peut rajouter d'autres parametres que les positions )
                world_state = {
                    "p1": (p1.x, p1.y),  # Position P1
                    "p2": (p2.x, p2.y)  # Position P2
                }
                network.send(world_state)
            else:
                # pas encore de client, on joue tout seul
                p1.update_inputs(my_inputs)
                tick_engine.update_tick()

        elif my_role == "CLIENT":
            # CLIEnT

            # on applique nos inputs immediatement sans verifs
            p2.update_inputs(my_inputs)

            # TICK
            # cela fait bouger P2 tout de suite pour eviter le lag
            tick_engine.update_tick()

            # on envoie nos inputs
            network.send(my_inputs)

            # on verifie avec les infos du serveur si on dit de la merde ou pas
            server_state = network.receive()
            if server_state:
                # le serveur me dit où est P1 (l'ennemi) --> maj instantannée
                p1.x, p1.y = server_state["p1"]

                # le serveur nous envoie notre vraie position
                # ici la "Reconciliation" entre nos infos et celle du serveur
                real_p2_x, real_p2_y = server_state["p2"]
                p2.reconcile(real_p2_x, real_p2_y)

        # --- 4. RENDER ---
        render.render_frame()
        clock.tick(60)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()