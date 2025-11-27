# imports
import sys
import pygame
from src.CoreEngine.EngineRender import EngineRender
from src.CoreEngine.EngineTick import EngineTick
from src.Entities.Player import Player
from src.Entities.Platform import Platform


def main():
    render_engine = EngineRender(800, 600)
    tick_engine = EngineTick()

    # Creation
    ground = Platform(0, 500, 800, 100)
    player = Player(100, 300)

    # Ajout au Render (Visuel)
    render_engine.add_object(ground)
    render_engine.add_object(player)

    # Ajout au Tick (Logique) -> On distingue entité et obstacle
    tick_engine.add_obstacle(ground)
    tick_engine.add_entity(player)

    running = True
    while running:

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        tick_engine.update_tick()
        render_engine.render_frame()

    pygame.quit()
    sys.exit()

main()