import pygame
from src.CoreEngine.SoundManager import SoundManager


class EngineTick:
    def __init__(self):
        self.objects     = []   # entités tickables (joueurs)
        self.obstacles   = []   # obstacles statiques (plateformes)
        self.projectiles = []   # projectiles actifs
        self.punish_events = [] # liste des punitions à consommer par l'UI : {"attacker": Player}

    def add_entity(self, obj):
        self.objects.append(obj)

    def add_obstacle(self, obj):
        self.obstacles.append(obj)

    def _emit_punish_event(self, attacker):
        """Enregistre un événement de punition pour que l'UI puisse l'afficher"""
        self.punish_events.append({"attacker": attacker})

    def update_tick(self):
        # Vidage des events de la frame précédente
        self.punish_events.clear()
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

        # 7. Collisions attaques mêlée / entités
        self.handle_attack_collisions()

        # 8. Collisions projectiles / entités
        self.handle_projectile_collisions()

    # ------------------------------------------------------------------ #
    #  SPAWN PROJECTILES
    # ------------------------------------------------------------------ #

    def _handle_projectile_spawn(self):
        """Crée le bon projectile selon le personnage qui tire."""
        from src.Entities.Projectile import RobotProjectile, LanceProjectile, ShurikenProjectile, ExplosionEffect

        for entity in self.objects:
            # --- Attack 1 : Robot (boule) ou Cromagnon (lance) ---
            if getattr(entity, 'wants_to_shoot', False):
                already = any(p for p in self.projectiles
                              if p.owner is entity and not isinstance(p, ShurikenProjectile))
                if not already:
                    direction = 1 if entity.facing_right else -1
                    hb = entity.hitbox

                    if entity.name == "Cromagnon":
                        shoulder_y = hb.top + int(hb.height * 0.15)   # ~15% depuis le haut = épaule
                        py = shoulder_y - LanceProjectile.SIZE[1] // 2
                        if direction == 1:
                            px = hb.centerx
                        else:
                            px = hb.centerx - LanceProjectile.SIZE[0]
                        proj = LanceProjectile(px, py, direction, owner=entity)
                    else:  # Robot
                        px = hb.right if direction == 1 else hb.left - RobotProjectile.SIZE[0]
                        py = hb.centery - RobotProjectile.SIZE[1] // 2 - 50
                        proj = RobotProjectile(px, py, direction, owner=entity)

                    self.projectiles.append(proj)

            # --- Attack 2 : Samourai (shuriken) ---
            if getattr(entity, 'wants_to_shoot2', False):
                already2 = any(p for p in self.projectiles
                               if p.owner is entity and isinstance(p, ShurikenProjectile))
                if not already2:
                    direction = 1 if entity.facing_right else -1
                    hb = entity.hitbox
                    px = hb.right if direction == 1 else hb.left - ShurikenProjectile.SIZE[0]
                    py = hb.centery - ShurikenProjectile.SIZE[1] // 2
                    proj = ShurikenProjectile(px, py, direction, owner=entity)
                    self.projectiles.append(proj)

            # --- Attack 2 Robot : explosion au sol ---
            if getattr(entity, 'wants_to_explode', False):
                direction = 1 if entity.facing_right else -1
                hb = entity.hitbox
                # Centré devant le Robot, calé au sol
                exp_w, exp_h = ExplosionEffect.SIZE
                px = (hb.right if direction == 1 else hb.left - exp_w) - exp_w // 4 * direction
                py = hb.bottom - exp_h + 20   # bas de l'explosion au niveau du sol
                proj = ExplosionEffect(px, py, direction, owner=entity)
                self.projectiles.append(proj)    # ------------------------------------------------------------------ #
    #  COLLISIONS ENTITÉS / OBSTACLES
    # ------------------------------------------------------------------ #

    def handle_collisions(self):
        """Collisions entités / plateformes (sol inclus)"""
        for entity in self.objects:
            entity.on_ground = False

        for entity in self.objects:
            for obstacle in self.obstacles:
                rect_entity   = entity.hitbox
                rect_obstacle = pygame.Rect(obstacle.x, obstacle.y, obstacle.width, obstacle.height)

                if rect_entity.colliderect(rect_obstacle):
                    if entity.velocity_y > 0:
                        entity.velocity_y = 0
                        entity.y          = obstacle.y - entity.height * entity.hitbox_height_ratio
                        entity.on_ground  = True
                        entity.jumps_remaining = 2   # recharge les deux sauts à l'atterrissage

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

                    a.x = max(0, min(1280 - a.width, a.x))
                    b.x = max(0, min(1280 - b.width, b.x))

    # ------------------------------------------------------------------ #
    #  COLLISIONS ATTAQUES MÊLÉE (Cromagnon / Samourai)
    # ------------------------------------------------------------------ #

    def handle_attack_collisions(self):
        """
        Vérifie si la hitbox d'attaque (1 ou 2) d'un joueur touche l'adversaire.
        """
        for attacker in self.objects:
            for attack_hb, damage in [
                (getattr(attacker, 'attack_hitbox',  None), attacker.attack_damage),
                (getattr(attacker, 'attack2_hitbox', None), attacker.attack2_damage),
            ]:
                if attack_hb is None:
                    continue

                for target in self.objects:
                    if target is attacker:
                        continue
                    if not target.is_alive:
                        continue

                    shield_hb = getattr(target, 'shield_hitbox', None)
                    hit_shield = shield_hb is not None and attack_hb.colliderect(shield_hb)
                    hit_body = attack_hb.colliderect(target.hitbox)

                    if hit_shield or hit_body:
                        was_punish = target.take_damage(damage)

                        # Son bouclier si le coup a été bloqué
                        if target.shielding:
                            sfx = SoundManager()
                            if getattr(target, 'perfect_shielded', False):
                                sfx.play("shield_perfect")
                            else:
                                sfx.play("shield")

                        # Attack lag sur l'attaquant
                        attacker.apply_attack_lag()

                        # Annule la phase active pour éviter les hits multiples
                        if attacker.attack_hitbox_active:
                            attacker.attack_hitbox_active = False
                            attacker.attack_phase  = "recovery"
                            attacker.attack_frame  = 0
                        if attacker.attack2_hitbox_active:
                            attacker.attack2_hitbox_active = False
                            attacker.attack2_phase = "recovery"
                            attacker.attack2_frame = 0

                        if was_punish:
                            self._emit_punish_event(attacker)

    # ------------------------------------------------------------------ #
    #  COLLISIONS PROJECTILES / ENTITÉS
    # ------------------------------------------------------------------ #

    def handle_projectile_collisions(self):
        """
        Vérifie si un projectile touche un joueur adverse.
        ExplosionEffect est exclu — ses dégâts viennent de attack2_hitbox du Player.
        """
        from src.Entities.Projectile import ExplosionEffect
        for proj in self.projectiles:
            if not proj.active:
                continue
            if isinstance(proj, ExplosionEffect):
                continue   # animation pure, pas de collision ici

            for target in self.objects:
                if target is proj.owner:
                    continue
                if not target.is_alive:
                    continue

                # --- Vérification bouclier en priorité ---
                shield_hb = getattr(target, 'shield_hitbox', None)
                if shield_hb is not None and proj.hitbox.colliderect(shield_hb):
                    target.take_damage(proj.DAMAGE)
                    proj.owner.apply_attack_lag()
                    proj.active = False
                    sfx = SoundManager()
                    if getattr(target, 'perfect_shielded', False):
                        sfx.play("shield_perfect")
                    else:
                        sfx.play("shield")
                    break

                # --- Vérification hitbox normale ---
                if proj.hitbox.colliderect(target.hitbox):
                    was_punish = target.take_damage(proj.DAMAGE)
                    proj.owner.apply_attack_lag()
                    proj.active = False

                    if was_punish:
                        self._emit_punish_event(proj.owner)
                    break

    # ------------------------------------------------------------------ #
    #  RENDU DES PROJECTILES
    # ------------------------------------------------------------------ #

    def render_projectiles(self, render_engine):
        """Appelé depuis EngineRender.render_frame() après les objets"""
        for proj in self.projectiles:
            proj.render(render_engine)