import pygame
from src.CoreEngine.EngineTick import EngineTick
from src.CoreEngine.EngineRender import EngineRender



class App:
    def __init__(self):
        self.running = True
        self.renderClass = EngineRender()
        self.tickClass = EngineTick()


    def execute(self):
        pygame.init()
        self.running = True
        screen = pygame.display.set_mode((800, 600))

        while self.running:
            if pygame.event.get(pygame.QUIT):
                self.running = False
                pygame.quit()

            self.tickClass.main()
            self.renderClass.main()



app = App()
app.execute()


