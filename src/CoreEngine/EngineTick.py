import pygame


class EngineTick:
    def __init__(self):
        self.objects = []       # entités tickables (joueurs)
        self.obstacles = []     # obstacles statiques (plateformes)
        self.projectiles = []   # projectiles actifs

    def add_entity(self, obj):
        self.objects.append(obj)

    def add_obstacle(self, obj):
        self.obstacles.append(obj)

    def update_tick(self):
        # 1. Tick de toutes les entités
        for obj in self.objects:
            obj.tick()

        # 2. Spawn de projectiles si un Robot a attaqué
        self._handle_projectile_spawn()

        # 3. Tick des projectiles existants
        for proj in self.projectiles:
            proj.tick()

        # 4. Suppression des projectiles inactifs
        self.projectiles = [p for p in self.projectiles if p.active]

        # 5. Collisions entités / obstacles
        self.handle_collisions()

        # 6. Collisions entités / entités (anti-traversée)
        self.handle_entity_collisions()

        # 7. Collisions attaques / entités
        self.handle_attack_collisions()

        # 8. Collisions projectiles / entités
        self.handle_projectile_collisions()

    # ------------------------------------------------------------------ #
    #  SPAWN PROJECTILES
    # ------------------------------------------------------------------ #

    def _handle_projectile_spawn(self):
        """Crée un projectile quand un Robot signale wants_to_shoot"""
        from src.Entities.Projectile import Projectile

        for entity in self.objects:
            if getattr(entity, 'wants_to_shoot', False):
                # Vérifie qu'aucune boule appartenant à ce joueur n'est déjà active
                already_shooting = any(p for p in self.projectiles if p.owner is entity)
                if already_shooting:
                    continue  # ← on ne tire pas si une boule est déjà en vol

                direction = 1 if entity.facing_right else -1
                hb = entity.hitbox
                # Le projectile part du côté avant du robot, centré verticalement
                px = hb.right if direction == 1 else hb.left - Projectile.SIZE[0]
                py = hb.centery - Projectile.SIZE[1] // 2 - 50
                proj = Projectile(px, py, direction, owner=entity)
                self.projectiles.append(proj)

    # ------------------------------------------------------------------ #
    #  COLLISIONS ENTITÉS / OBSTACLES
    # ------------------------------------------------------------------ #

    def handle_collisions(self):
        """Collisions entités / plateformes (sol inclus)"""
        for entity in self.objects:
            entity.on_ground = False  # reset chaque frame, rétabli si collision détectée

        for entity in self.objects:
            for obstacle in self.obstacles:
                rect_entity = entity.hitbox
                rect_obstacle = pygame.Rect(obstacle.x, obstacle.y, obstacle.width, obstacle.height)

                if rect_entity.colliderect(rect_obstacle):
                    if entity.velocity_y > 0:
                        entity.velocity_y = 0
                        entity.y = obstacle.y - entity.height * entity.hitbox_height_ratio
                        entity.on_ground = True

    # ------------------------------------------------------------------ #
    #  COLLISIONS ENTITÉS / ENTITÉS
    # ------------------------------------------------------------------ #

    def handle_entity_collisions(self):
        """Empêche les joueurs de se traverser"""
        if len(self.objects) < 2:
            return

        for i in range(len(self.objects)):
            for j in range(i + 1, len(self.objects)):
                a = self.objects[i]
                b = self.objects[j]

                rect_a = a.hitbox
                rect_b = b.hitbox

                if rect_a.colliderect(rect_b):
                    overlap_left  = rect_a.right - rect_b.left
                    overlap_right = rect_b.right - rect_a.left

                    if overlap_left < overlap_right:
                        correction = overlap_left // 2
                        a.x -= correction
                        b.x += correction
                    else:
                        correction = overlap_right // 2
                        a.x += correction
                        b.x -= correction

                    # Clamp : pas de sortie d'écran
                    a.x = max(0, min(1280 - a.width, a.x))
                    b.x = max(0, min(1280 - b.width, b.x))

    # ------------------------------------------------------------------ #
    #  COLLISIONS ATTAQUES MÊLÉE (Cromagnon)
    # ------------------------------------------------------------------ #

    def handle_attack_collisions(self):
        """Vérifie si la hitbox d'attaque d'un joueur touche l'adversaire"""
        for attacker in self.objects:
            attack_hb = getattr(attacker, 'attack_hitbox', None)
            if attack_hb is None:
                continue

            for target in self.objects:
                if target is attacker:
                    continue
                if not target.is_alive:
                    continue

                if attack_hb.colliderect(target.hitbox):
                    target.take_damage(attacker.attack_damage)
                    # On désactive la hitbox immédiatement pour ne blesser qu'une fois
                    attacker.attack_hitbox_active = False
                    attacker.attack_phase = "recovery"
                    attacker.attack_frame = 0

    # ------------------------------------------------------------------ #
    #  COLLISIONS PROJECTILES / ENTITÉS
    # ------------------------------------------------------------------ #

    def handle_projectile_collisions(self):
        """Vérifie si un projectile touche un joueur adverse"""
        for proj in self.projectiles:
            if not proj.active:
                continue

            for target in self.objects:
                # Ne pas blesser le tireur
                if target is proj.owner:
                    continue
                if not target.is_alive:
                    continue

                if proj.hitbox.colliderect(target.hitbox):
                    target.take_damage(proj.DAMAGE)
                    proj.active = False  # projectile consommé
                    break

    # ------------------------------------------------------------------ #
    #  RENDU DES PROJECTILES (appelé par EngineRender via render_frame)
    # ------------------------------------------------------------------ #

    def render_projectiles(self, render_engine):
        """À appeler depuis EngineRender.render_frame() après les objets"""
        for proj in self.projectiles:
            proj.render(render_engine)