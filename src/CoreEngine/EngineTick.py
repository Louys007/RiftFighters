import pygame

class EngineTick:
    def __init__(self):
        self.objects = [] # liste des objets a ticker chaque frame
        self.obstacles = [] # liste des obstacles (plateforme)

    def add_entity(self, obj):
        self.objects.append(obj)

    def add_obstacle(self, obj):
        self.obstacles.append(obj)

    def update_tick(self):
        for obj in self.objects: # fait ticker tous les acteurs enregistrés
            obj.tick()
        self.handle_collisions()


    ## Cette classe fonctionnera conjointement avec la classe de collisions car elle (la classe EngineTick) fournira les données necessaires pour verifier les collisions
    def handle_collisions(self):
        for entity in self.objects:
            for obstacle in self.obstacles:


                rect1 = pygame.Rect(entity.x, entity.y, entity.width, entity.height)
                rect2 = pygame.Rect(obstacle.x, obstacle.y, obstacle.width, obstacle.height)

                if rect1.colliderect(rect2): ## est ce qu'il y a une collision
                    if entity.velocity_y > 0:
                        entity.velocity_y = 0
                        entity.y = obstacle.y - entity.height
                        entity.on_ground = True

