class Platform():
    def __init__(self, x, y, width, height, color = (100,200,100)):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.color = color
        self.rect = None

    def tick(self):
        pass

    def render(self, EngineRender):
        EngineRender.drawCube(self.x, self.y, self.width, self.height, self.color)