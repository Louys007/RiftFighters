import pygame
import os
from ..Utils.UtilsFunctions import *


# --- Personnages qui utilisent une attaque de mêlée ---
MELEE_CHARACTERS = {"Cromagnon", "Samourai"}

# --- Définition des frames d'attaque par personnage ---
ATTACK_DATA = {
    "Cromagnon": {
        "startup":  4,
        "active":   6,
        "recovery": 8,
        "damage":   12,
        "hitbox_reach":  120,
        "hitbox_height": 60,
    },
    "Robot": {
        "startup":  6,
        "active":   3,
        "recovery": 10,
        "damage":   18,
    },
    "Samourai": {
        "startup":  3,
        "active":   5,
        "recovery": 10,
        "damage":   15,
        "hitbox_reach":  140,
        "hitbox_height": 55,
    }
}

# --- Bouclier ---
SHIELD_DAMAGE_RATIO    = 0.20
SHIELD_COOLDOWN_FRAMES = 30
SHIELD_RADIUS_RATIO    = 0.5

# --- Dash ---
DASH_DISTANCE      = 200   # px parcourus pendant le dash
DASH_DURATION      = 8     # frames de déplacement
DASH_COOLDOWN      = 20    # frames avant de pouvoir redash
DASH_DOUBLE_TAP    = 15    # fenêtre en frames pour le double-tap


class Player:
    def __init__(self, x, y, config):
        # --- Système de prédiction réseau ---
        self.pending_inputs = []

        self.x = x
        self.y = y
        self.facing_right = True
        self.name = config.get('name', 'Cromagnon')

        wanted_size = config.get('size', None)
        image_path = os.path.join("assets", "Perso", config['image'])

        # --- Chargement sprite IDLE ---
        self.sprite_idle = None
        try:
            loaded_img = pygame.image.load(image_path).convert_alpha()
            if wanted_size is None:
                wanted_size = loaded_img.get_size()
            self.sprite_idle = pygame.transform.scale(loaded_img, wanted_size)
            self.width  = self.sprite_idle.get_width()
            self.height = self.sprite_idle.get_height()
        except Exception as e:
            print(f"Erreur chargement idle {image_path}: {e}")
            self.width  = 50
            self.height = 50
            self.sprite_idle = None
            self.color = (255, 0, 255)

        # --- Chargement sprite WALK ---
        walk_path = image_path.replace("_idle", "_walk")
        try:
            walk_img = pygame.image.load(walk_path).convert_alpha()
            self.sprite_walk = pygame.transform.scale(walk_img, wanted_size)
        except:
            self.sprite_walk = self.sprite_idle

        # --- Chargement sprite JUMP ---
        jump_path = image_path.replace("_idle", "_jump")
        try:
            jump_img = pygame.image.load(jump_path).convert_alpha()
            self.sprite_jump = pygame.transform.scale(jump_img, wanted_size)
        except:
            self.sprite_jump = self.sprite_idle

        # --- Chargement sprite ATTACK ---
        attack_path = image_path.replace("_idle", "_attack_1")
        try:
            attack_img = pygame.image.load(attack_path).convert_alpha()
            self.sprite_attack = pygame.transform.scale(attack_img, wanted_size)
        except:
            self.sprite_attack = self.sprite_idle

        self.sprite = self.sprite_idle

        # --- Hitbox ---
        self.hitbox_width_ratio  = config.get('hitbox_width_ratio', 0.5)
        self.hitbox_height_ratio = config.get('hitbox_height_ratio', 0.9)

        # --- Animation ---
        self.anim_timer    = 0
        self.anim_interval = 8
        self.is_moving     = False

        # --- Stats ---
        self.speed         = config.get('speed', 16)
        self.jump_strength = config.get('jump', -30)
        self.gravity       = config.get('gravity', 2)

        # --- Physique ---
        self.velocity_y = 0
        self.on_ground  = False
        self.inputs = {
            "left": False, "right": False,
            "jump": False, "attack": False, "shield": False
        }

        # --- Vie ---
        self.max_health = 100
        self.health     = self.max_health
        self.is_alive   = True

        # --- Attaque ---
        attack_info = ATTACK_DATA.get(self.name, ATTACK_DATA["Cromagnon"])
        self.attack_startup  = attack_info["startup"]
        self.attack_active   = attack_info["active"]
        self.attack_recovery = attack_info["recovery"]
        self.attack_damage   = attack_info["damage"]
        self.attack_reach    = attack_info.get("hitbox_reach", 120)
        self.attack_height   = attack_info.get("hitbox_height", 60)

        self.attack_phase         = None
        self.attack_frame         = 0
        self.attack_hitbox_active = False
        self.wants_to_shoot       = False
        self.attack_input_prev    = False

        # --- Bouclier ---
        self.shielding         = False
        self.shield_cooldown   = 0
        self.shield_input_prev = False

        # --- Dash ---
        # État courant
        self.is_dashing      = False
        self.dash_frame      = 0        # frames écoulées depuis le début du dash
        self.dash_direction  = 0        # +1 ou -1
        self.dash_speed      = DASH_DISTANCE / DASH_DURATION  # px/frame

        # Cooldown après dash
        self.dash_cooldown   = 0

        # Détection double-tap gauche
        self.left_tap_count  = 0        # nb d'appuis enregistrés
        self.left_tap_timer  = 0        # frames depuis le premier appui
        self.left_prev       = False    # état précédent de la touche

        # Détection double-tap droite
        self.right_tap_count = 0
        self.right_tap_timer = 0
        self.right_prev      = False

    # ------------------------------------------------------------------ #
    #  PROPRIÉTÉS
    # ------------------------------------------------------------------ #

    @property
    def hitbox(self):
        hw = self.width  * self.hitbox_width_ratio
        hh = self.height * self.hitbox_height_ratio
        hx = self.x + (self.width - hw) / 2
        hy = self.y + (self.height - hh)
        return pygame.Rect(hx, hy, hw, hh)

    @property
    def shield_hitbox(self):
        if not self.shielding:
            return None
        hb     = self.hitbox
        radius = int(max(hb.width, hb.height) * SHIELD_RADIUS_RATIO)
        return pygame.Rect(hb.centerx - radius, hb.centery - radius, radius * 2, radius * 2)

    @property
    def attack_hitbox(self):
        if self.name not in MELEE_CHARACTERS or not self.attack_hitbox_active:
            return None
        hb = self.hitbox
        ax = hb.right if self.facing_right else hb.left - self.attack_reach
        ay = hb.centery - self.attack_height // 2
        return pygame.Rect(ax, ay, self.attack_reach, self.attack_height)

    @property
    def is_attacking(self):
        return self.attack_phase is not None

    @property
    def is_stunned(self):
        return self.shield_cooldown > 0

    # ------------------------------------------------------------------ #
    #  MÉTHODES PUBLIQUES
    # ------------------------------------------------------------------ #

    def take_damage(self, amount):
        if self.is_alive:
            if self.shielding:
                amount = int(amount * SHIELD_DAMAGE_RATIO)
            self.health = max(0, self.health - amount)
            if self.health <= 0:
                self.is_alive = False
                self.health   = 0

    def heal(self, amount):
        if self.is_alive:
            self.health = min(self.max_health, self.health + amount)

    def update_inputs(self, keys):
        self.inputs = keys

    def face_opponent(self, opponent):
        if opponent is None or not opponent.is_alive:
            return
        if opponent.x > self.x:
            self.facing_right = True
        else:
            self.facing_right = False

    # ------------------------------------------------------------------ #
    #  DÉTECTION DOUBLE-TAP
    # ------------------------------------------------------------------ #

    def _update_double_tap(self):
        """
        Détecte un double-tap sur gauche ou droite.
        Retourne la direction du dash (+1 droite, -1 gauche) ou 0.
        """
        left  = self.inputs.get("left",  False)
        right = self.inputs.get("right", False)

        dash_dir = 0

        # --- Gauche ---
        if self.left_tap_count > 0:
            self.left_tap_timer += 1
            if self.left_tap_timer > DASH_DOUBLE_TAP:
                # Fenêtre expirée, on remet à zéro
                self.left_tap_count = 0
                self.left_tap_timer = 0

        # Front montant gauche
        if left and not self.left_prev:
            self.left_tap_count += 1
            if self.left_tap_count == 1:
                self.left_tap_timer = 0
            elif self.left_tap_count >= 2:
                dash_dir = -1
                self.left_tap_count = 0
                self.left_tap_timer = 0

        self.left_prev = left

        # --- Droite ---
        if self.right_tap_count > 0:
            self.right_tap_timer += 1
            if self.right_tap_timer > DASH_DOUBLE_TAP:
                self.right_tap_count = 0
                self.right_tap_timer = 0

        if right and not self.right_prev:
            self.right_tap_count += 1
            if self.right_tap_count == 1:
                self.right_tap_timer = 0
            elif self.right_tap_count >= 2:
                dash_dir = 1
                self.right_tap_count = 0
                self.right_tap_timer = 0

        self.right_prev = right

        return dash_dir

    # ------------------------------------------------------------------ #
    #  TICK
    # ------------------------------------------------------------------ #

    def tick(self):
        if not self.is_alive:
            return

        # Reset flags one-shot
        self.attack_hitbox_active = False
        self.wants_to_shoot       = False

        # --- Cooldown bouclier (stun) ---
        if self.shield_cooldown > 0:
            self.shield_cooldown -= 1
            self.shielding = False
            self.is_moving = False
            if self.dash_cooldown > 0:
                self.dash_cooldown -= 1
            self.apply_gravity()
            return

        # --- Cooldown dash ---
        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1

        # --- Dash en cours ---
        if self.is_dashing:
            self.dash_frame += 1
            # Déplacement horizontal du dash — les persos peuvent se traverser
            new_x = self.x + self.dash_speed * self.dash_direction
            # On clamp seulement les bords d'écran
            self.x = max(0, min(1280 - self.width, new_x))

            if self.dash_frame >= DASH_DURATION:
                self.is_dashing   = False
                self.dash_frame   = 0
                self.dash_cooldown = DASH_COOLDOWN

            self.is_moving = True
            # Animation et gravité continuent pendant le dash
            self.anim_timer += 1
            if self.anim_timer >= self.anim_interval:
                self.anim_timer = 0
            self.apply_gravity()
            return

        # --- Gestion du bouclier ---
        shield_pressed = self.inputs.get("shield", False)
        can_shield     = self.on_ground and not self.is_attacking

        if shield_pressed and can_shield:
            self.shielding = True
        else:
            if self.shielding and not shield_pressed:
                self.shield_cooldown = SHIELD_COOLDOWN_FRAMES
            self.shielding = False

        self.shield_input_prev = shield_pressed

        if self.shielding:
            self.is_moving = False
            self.apply_gravity()
            return

        # --- Détection double-tap (dash) ---
        # Interdit pendant attaque ou bouclier
        if not self.is_attacking and not self.shielding and self.dash_cooldown <= 0:
            dash_dir = self._update_double_tap()
            if dash_dir != 0:
                self.is_dashing     = True
                self.dash_frame     = 0
                self.dash_direction = dash_dir
                self.facing_right   = (dash_dir == 1)
                self.anim_timer += 1
                if self.anim_timer >= self.anim_interval:
                    self.anim_timer = 0
                self.apply_gravity()
                return
        else:
            # On met quand même à jour les états prev pour éviter les faux double-taps
            self._update_double_tap()

        # --- Gestion de l'attaque ---
        attack_pressed = self.inputs.get("attack", False)

        if self.attack_phase is None:
            if attack_pressed and not self.attack_input_prev:
                self.attack_phase = "startup"
                self.attack_frame = 0
        else:
            self.attack_frame += 1

            if self.attack_phase == "startup":
                if self.attack_frame >= self.attack_startup:
                    self.attack_phase = "active"
                    self.attack_frame = 0

            elif self.attack_phase == "active":
                self.attack_hitbox_active = True
                if self.name == "Robot" and self.attack_frame == 1:
                    self.wants_to_shoot = True
                if self.attack_frame >= self.attack_active:
                    self.attack_phase = "recovery"
                    self.attack_frame = 0

            elif self.attack_phase == "recovery":
                if self.attack_frame >= self.attack_recovery:
                    self.attack_phase = None
                    self.attack_frame = 0

        self.attack_input_prev = attack_pressed

        # --- Déplacement normal (bloqué pendant l'attaque) ---
        self.is_moving = False

        if not self.is_attacking:
            if self.inputs["left"] and self.x > 0:
                self.x -= self.speed
                self.is_moving    = True
                self.facing_right = False

            if self.inputs["right"] and self.x < 1280 - self.width:
                self.x += self.speed
                self.is_moving    = True
                self.facing_right = True

        # --- Saut ---
        if self.inputs["jump"] and self.on_ground and self.attack_phase != "recovery":
            self.velocity_y = self.jump_strength
            self.on_ground  = False

        # --- Timer animation ---
        self.anim_timer += 1
        if self.anim_timer >= self.anim_interval:
            self.anim_timer = 0

        self.apply_gravity()

    def apply_gravity(self):
        self.velocity_y += self.gravity
        self.y += self.velocity_y

    # ------------------------------------------------------------------ #
    #  RENDU
    # ------------------------------------------------------------------ #

    def render(self, RenderEngine):
        if self.sprite_idle:
            # Choix du sprite (priorité : attaque > saut > marche/dash > idle)
            if self.is_attacking:
                image_to_draw = self.sprite_attack
            elif not self.on_ground:
                image_to_draw = self.sprite_jump
            elif self.is_moving or self.is_dashing:
                frame = self.anim_timer // (self.anim_interval // 2)
                image_to_draw = self.sprite_walk if frame == 0 else self.sprite_idle
            else:
                image_to_draw = self.sprite_idle

            if not self.facing_right:
                image_to_draw = pygame.transform.flip(image_to_draw, True, False)

            # Effet visuel pendant le dash : légère transparence
            if self.is_dashing:
                image_to_draw = image_to_draw.copy()
                image_to_draw.set_alpha(160)
            elif not self.is_alive:
                image_to_draw = image_to_draw.copy()
                image_to_draw.set_alpha(100)

            RenderEngine.internal_surface.blit(image_to_draw, (int(self.x), int(self.y)))

            # --- Bulle bouclier ---
            if self.shielding:
                hb     = self.hitbox
                radius = int(max(hb.width, hb.height) * SHIELD_RADIUS_RATIO)
                cx     = int(hb.centerx)
                cy     = int(hb.centery)
                bubble_size = radius * 2 + 10
                bubble_surf = pygame.Surface((bubble_size, bubble_size), pygame.SRCALPHA)
                pygame.draw.circle(bubble_surf, (180, 180, 220, 80),  (bubble_size // 2, bubble_size // 2), radius)
                pygame.draw.circle(bubble_surf, (200, 200, 255, 180), (bubble_size // 2, bubble_size // 2), radius, 3)
                RenderEngine.internal_surface.blit(bubble_surf, (cx - bubble_size // 2, cy - bubble_size // 2))

            # --- Barre cooldown bouclier ---
            if self.shield_cooldown > 0:
                hb    = self.hitbox
                bar_w = int(hb.width)
                bar_h = 5
                bar_x = int(hb.x)
                bar_y = int(hb.y) - 12
                ratio = self.shield_cooldown / SHIELD_COOLDOWN_FRAMES
                pygame.draw.rect(RenderEngine.internal_surface, (50, 50, 50),    (bar_x, bar_y, bar_w, bar_h))
                pygame.draw.rect(RenderEngine.internal_surface, (100, 180, 255), (bar_x, bar_y, int(bar_w * ratio), bar_h))

            # --- Indicateur cooldown dash (barre orange sous le perso) ---
            if self.dash_cooldown > 0:
                hb    = self.hitbox
                bar_w = int(hb.width)
                bar_h = 4
                bar_x = int(hb.x)
                bar_y = int(hb.bottom) + 4
                ratio = self.dash_cooldown / DASH_COOLDOWN
                pygame.draw.rect(RenderEngine.internal_surface, (50, 30, 0),     (bar_x, bar_y, bar_w, bar_h))
                pygame.draw.rect(RenderEngine.internal_surface, (255, 160, 30),  (bar_x, bar_y, int(bar_w * ratio), bar_h))

            # Debug hitbox attaque (décommenter pour visualiser)
            # if self.attack_hitbox:
            #     pygame.draw.rect(RenderEngine.internal_surface, (255, 0, 0), self.attack_hitbox, 2)

        else:
            color = self.color if self.is_alive else (100, 100, 100)
            RenderEngine.drawCube(self.x, self.y, self.width, self.height, color)

    # ------------------------------------------------------------------ #
    #  RÉSEAU
    # ------------------------------------------------------------------ #

    def predict_movement(self, seq, inputs):
        self.pending_inputs.append({"seq": seq, "inputs": inputs})
        self.apply_movement_only(inputs)

    def apply_movement_only(self, keys):
        if keys.get("left", False) and self.x > 0:
            self.x -= self.speed
            self.facing_right = False
        if keys.get("right", False) and self.x < 1280 - self.width:
            self.x += self.speed
            self.facing_right = True

    def reconcile(self, server_x, server_y, ack_seq):
        if server_x > self.x:
            self.facing_right = True
        elif server_x < self.x:
            self.facing_right = False
        self.x = server_x
        self.y = server_y
        self.pending_inputs = [p for p in self.pending_inputs if p["seq"] > ack_seq]
        for pending in self.pending_inputs:
            self.apply_movement_only(pending["inputs"])