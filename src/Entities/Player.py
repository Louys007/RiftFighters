import pygame
import os
from ..Utils.UtilsFunctions import *
from ..CoreEngine.SoundManager import SoundManager

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


# --- Personnages qui utilisent une attaque de mêlée ---
MELEE_CHARACTERS = {"Cromagnon", "Samourai", "Chevalier"}

# --- Définition des frames d'attaque par personnage ---
# À 30 Hz : 1 frame ≈ 33 ms
#
# Cromagnon — mêlée équilibrée
#   startup  6f (~200ms)  : armement visible, peut être interrompu
#   active   5f (~167ms)  : fenêtre de hit courte, récompense le timing
#   recovery 28f (~933ms) : lourd après chaque coup, spam impossible
#
# Robot — distance, fort mais très lent à relancer
#   startup  8f (~267ms)  : temps de charge du canon
#   active   2f (~67ms)   : boule part vite
#   recovery 45f (~1.5s)  : punition très sévère si raté ou bloqué
#
# Samourai — mêlée rapide mais recovery longue
#   startup  3f (~100ms)  : très rapide à sortir
#   active   4f (~133ms)  : fenêtre de hit courte
#   recovery 22f (~733ms) : punissable malgré la vitesse
ATTACK_DATA = {
    "Cromagnon": {
        "startup":  6,
        "active":   5,
        "recovery": 28,
        "damage":   12,
        "hitbox_reach":  120,
        "hitbox_height": 60,
        "y_offset": -40
    },
    "Robot": {
        "startup":  8,
        "active":   2,
        "recovery": 45,
        "damage":   18,
    },
    "Samourai": {
        "startup":  3,
        "active":   4,
        "recovery": 22,
        "damage":   15,
        "hitbox_reach":  140,
        "hitbox_height": 55,
        "y_offset": -30,
    },
    "Chevalier": {
        "startup":  5,
        "active":   6,
        "recovery": 24,
        "damage":   16,
        "hitbox_reach":  80,
        "hitbox_height": 150,
        "y_offset": 0,
    }
}

# --- Attaque 2 : coup spécial distinct par personnage ---
# Cromagnon  : frappe vers le bas (coup de masse) — portée courte mais haute
# Robot      : tir chargé (pas de boule, zone électrique au corps-à-corps)
# Samourai   : estocade perçante — portée très longue, fenêtre active très courte
ATTACK2_DATA = {
    "Cromagnon": {
        "startup":  10,
        "active":   4,
        "recovery": 32,
        "damage":   20,
        "hitbox_reach":  80,
        "hitbox_height": 100,   # zone haute et courte
    },
    "Robot": {
        "startup":  12,
        "active":   16,   # 4 frames × 4 images = animation complète
        "recovery": 35,
        "damage":   25,
        "hitbox_reach":  160,
        "hitbox_height": 120,
    },
    "Samourai": {
        "startup":  5,
        "active":   2,
        "recovery": 28,
        "damage":   22,
        "hitbox_reach":  220,   # très longue portée
        "hitbox_height": 35,    # zone fine
    },
    "Chevalier": {
        # Ruée : startup long (élan), active long (déplacement), recovery longue (risqué si raté)
        "startup":  8,
        "active":   10,
        "recovery": 30,
        "damage":   22,
        "hitbox_reach":  200,
        "hitbox_height": 70,
    }
}

# --- Bouclier ---
SHIELD_DAMAGE_RATIO    = 0.20
SHIELD_COOLDOWN_FRAMES = 30
SHIELD_RADIUS_RATIO    = 0.5
PERFECT_SHIELD_WINDOW  = 6    # frames après activation du bouclier = perfect shield

# --- Hit stun (freeze quand on reçoit un coup) ---
HIT_STUN_FRAMES        = 12   # frames de gel à la réception d'un coup normal
HIT_STUN_FRAMES_SHIELD = 6    # frames de gel quand on bloque avec le bouclier
PUNISH_HIT_STUN_FRAMES = 18   # frames de gel lors d'une punition (coup sur recovery)

# --- Attack lag (freeze après avoir frappé) ---
ATTACK_LAG_FRAMES      = 8    # frames de gel pour l'attaquant après un hit normal

# --- Punition ---
PUNISH_DAMAGE_MULTIPLIER = 2.0  # dégâts ×2 si la cible est en recovery

# --- Dash ---
DASH_DISTANCE      = 200   # px parcourus pendant le dash
DASH_DURATION      = 8     # frames de déplacement
DASH_COOLDOWN      = 20    # frames avant de pouvoir redash
DASH_DOUBLE_TAP    = 15    # fenêtre en frames pour le double-tap


class Player:
    def __init__(self, x, y, config):
        # --- Système de prédiction réseau ---
        self.pending_inputs = []
        self.opponent = None  # <-- AJOUT : Référence vers l'adversaire

        self.x = x
        self.y = y
        self.facing_right = True
        self.name = config.get('name', 'Cromagnon')

        wanted_size = config.get('size', None)
        image_path = os.path.join(_PROJECT_ROOT, "assets", "Perso", config['image'])

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

        # --- Chargement sprite ATTACK 2 ---
        attack2_path = image_path.replace("_idle", "_attack_2")
        try:
            attack2_img = pygame.image.load(attack2_path).convert_alpha()
            self.sprite_attack2 = pygame.transform.scale(attack2_img, wanted_size)
        except:
            self.sprite_attack2 = self.sprite_attack  # fallback sur attack1

        # --- Chargement sprite HURT (stun à la réception d'un coup) ---
        hit_path = image_path.replace("_idle", "_hurt")
        try:
            hit_img = pygame.image.load(hit_path).convert_alpha()
            self.sprite_hit = pygame.transform.scale(hit_img, wanted_size)
        except:
            self.sprite_hit = self.sprite_idle  # fallback silencieux si absent

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
        self.velocity_y    = 0
        self.on_ground     = False
        self.jumps_remaining = 2   # double saut : 2 sauts disponibles, rechargés à l'atterrissage
        self.jump_prev     = False # pour détecter le front montant de la touche saut
        self.inputs = {
            "left": False, "right": False,
            "jump": False, "attack": False, "attack2": False, "shield": False
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
        self.attack_y_offset = attack_info.get("y_offset", 0)

        self.attack_phase         = None
        self.attack_frame         = 0
        self.attack_hitbox_active = False
        self.wants_to_shoot       = False
        self.attack_input_prev    = False

        # --- Attaque 2 ---
        attack2_info = ATTACK2_DATA.get(self.name, ATTACK2_DATA["Cromagnon"])
        self.attack2_startup  = attack2_info["startup"]
        self.attack2_active   = attack2_info["active"]
        self.attack2_recovery = attack2_info["recovery"]
        self.attack2_damage   = attack2_info["damage"]
        self.attack2_reach    = attack2_info.get("hitbox_reach", 90)
        self.attack2_height   = attack2_info.get("hitbox_height", 80)
        self.attack2_y_offset = attack2_info.get("y_offset", 0)

        self.attack2_phase         = None
        self.attack2_frame         = 0
        self.attack2_hitbox_active = False
        self.wants_to_shoot2       = False
        self.wants_to_explode      = False   # Robot : explosion au sol
        self.attack2_input_prev    = False

        # --- Bouclier ---
        self.shielding                 = False
        self.shield_cooldown           = 0
        self.shield_input_prev         = False
        self.shield_age                = 0
        self.perfect_shielded          = False  # True tant que le bouclier parfait est actif ce cycle
        self.perfect_shield_triggered  = False  # one-shot : True une seule frame pour l'UI

        # --- Hit Stun (freeze à la réception d'un coup) ---
        self.hit_stun          = 0   # frames restantes de gel

        # --- Attack Lag (freeze après avoir frappé) ---
        self.attack_lag        = 0   # frames restantes de gel post-hit

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
        ay = hb.centery - self.attack_height // 2 + self.attack_y_offset
        return pygame.Rect(ax, ay, self.attack_reach, self.attack_height)

    @property
    def attack2_hitbox(self):
        """Hitbox de l'attaque 2 — active pour tous les personnages (y compris Robot en mêlée)."""
        if not self.attack2_hitbox_active:
            return None
        hb = self.hitbox
        ax = hb.right if self.facing_right else hb.left - self.attack2_reach
        ay = hb.centery - self.attack2_height // 2 + self.attack2_y_offset
        return pygame.Rect(ax, ay, self.attack2_reach, self.attack2_height)

    @property
    def is_attacking(self):
        return self.attack_phase is not None or self.attack2_phase is not None

    @property
    def is_in_recovery(self):
        """True quand le joueur est dans la phase de recovery — punissable"""
        return self.attack_phase == "recovery" or self.attack2_phase == "recovery"

    @property
    def is_stunned(self):
        return self.shield_cooldown > 0 or self.hit_stun > 0 or self.attack_lag > 0

    # ------------------------------------------------------------------ #
    #  MÉTHODES PUBLIQUES
    # ------------------------------------------------------------------ #

    def set_opponent(self, opponent):
        self.opponent = opponent

    def take_damage(self, amount):
        """
        Applique les dégâts. Retourne True si c'était une punition (cible en recovery).

        Règles de stun :
        - Coup reçu pendant le bouclier  → dégâts réduits, hit_stun court, shield_cooldown reset
        - Coup reçu en recovery (punition) → dégâts ×2, hit_stun long, recovery annulée
        - Coup reçu pendant startup/active → attaque interrompue, hit_stun normal
        - Coup reçu pendant shield_cooldown → cooldown annulé, hit_stun normal
        - Coup normal                      → hit_stun normal
        Dans tous les cas attack_lag est remis à zéro (le hit prime).
        """
        if not self.is_alive:
            return False

        was_punish = self.is_in_recovery

        # --- Cas bouclier actif ---
        if self.shielding:
            if self.shield_age <= PERFECT_SHIELD_WINDOW:
                amount = 0
                self.hit_stun                 = 0
                self.perfect_shielded         = True
                self.perfect_shield_triggered = True   # one-shot pour l'UI
            else:
                amount        = int(amount * SHIELD_DAMAGE_RATIO)
                self.hit_stun = HIT_STUN_FRAMES_SHIELD

        # --- Cas punition (recovery) ---
        elif was_punish:
            amount        = int(amount * PUNISH_DAMAGE_MULTIPLIER)
            self.hit_stun = PUNISH_HIT_STUN_FRAMES
            # Interrompt la recovery
            self.attack_phase  = None
            self.attack_frame  = 0
            self.attack2_phase = None
            self.attack2_frame = 0

        # --- Coup reçu pendant startup ou active → interrompt l'attaque ---
        elif self.attack_phase in ("startup", "active") or self.attack2_phase in ("startup", "active"):
            self.hit_stun      = HIT_STUN_FRAMES
            self.attack_phase  = None
            self.attack_frame  = 0
            self.attack2_phase = None
            self.attack2_frame = 0

        # --- Coup reçu pendant le stun de bouclier → reset le cooldown ---
        elif self.shield_cooldown > 0:
            self.shield_cooldown = 0
            self.hit_stun        = HIT_STUN_FRAMES

        # --- Coup normal ---
        else:
            self.hit_stun = HIT_STUN_FRAMES

        # L'attack_lag est toujours annulé par un hit reçu
        self.attack_lag = 0

        self.health = max(0, self.health - amount)
        if amount > 0:
            SoundManager().play("damage")
        if self.health <= 0:
            self.is_alive = False
            self.health   = 0

        return was_punish

    def apply_attack_lag(self):
        """Freeze l'attaquant après avoir touché — appelé par EngineTick"""
        self.attack_lag = ATTACK_LAG_FRAMES

    def heal(self, amount):
        if self.is_alive:
            self.health = min(self.max_health, self.health + amount)

    def update_inputs(self, keys):
        self.inputs = keys

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
        self.attack_hitbox_active  = False
        self.attack2_hitbox_active = False
        self.wants_to_shoot        = False
        self.wants_to_shoot2       = False
        self.wants_to_explode      = False
        self.perfect_shield_triggered = False  # reset chaque frame

        # --- Hit Stun : le joueur est gelé après avoir reçu un coup ---
        if self.hit_stun > 0:
            self.hit_stun -= 1
            self.is_moving = False
            if self.dash_cooldown > 0:
                self.dash_cooldown -= 1
            self.apply_gravity()
            return

        # --- Attack Lag : l'attaquant est gelé un instant après avoir frappé ---
        if self.attack_lag > 0:
            self.attack_lag -= 1
            self.is_moving = False
            self.apply_gravity()
            return

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
            if not self.shielding:
                self.shield_age       = 0
                self.perfect_shielded = False   # reset à chaque nouvelle activation
            else:
                self.shield_age += 1
            self.shielding = True
        else:
            if self.shielding and not shield_pressed:
                if self.perfect_shielded:
                    pass   # perfect shield : pas de cooldown
                else:
                    self.shield_cooldown = SHIELD_COOLDOWN_FRAMES
            self.shielding        = False
            self.shield_age       = 0
            self.perfect_shielded = False

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
                SoundManager().play("dash")
                self.anim_timer += 1
                if self.anim_timer >= self.anim_interval:
                    self.anim_timer = 0
                self.apply_gravity()
                return
        else:
            # On met quand même à jour les états prev pour éviter les faux double-taps
            self._update_double_tap()

        # --- Gestion de l'attaque 1 ---
        attack_pressed = self.inputs.get("attack", False)

        if self.attack_phase is None and self.attack2_phase is None:
            if attack_pressed and not self.attack_input_prev:
                self.attack_phase = "startup"
                self.attack_frame = 0
        elif self.attack_phase is not None:
            self.attack_frame += 1

            if self.attack_phase == "startup":
                if self.attack_frame >= self.attack_startup:
                    self.attack_phase = "active"
                    self.attack_frame = 0
                    SoundManager().play_for(self.name, "attack1")

            elif self.attack_phase == "active":
                # Tous les persos ont une hitbox mêlée sur attack1
                self.attack_hitbox_active = True
                # Robot uniquement : attack1 tire un projectile
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

        # --- Gestion de l'attaque 2 ---
        attack2_pressed = self.inputs.get("attack2", False)

        if self.attack_phase is None and self.attack2_phase is None:
            if attack2_pressed and not self.attack2_input_prev:
                self.attack2_phase = "startup"
                self.attack2_frame = 0
        elif self.attack2_phase is not None:
            self.attack2_frame += 1

            if self.attack2_phase == "startup":
                if self.attack2_frame >= self.attack2_startup:
                    self.attack2_phase = "active"
                    self.attack2_frame = 0
                    SoundManager().play_for(self.name, "attack2")

            elif self.attack2_phase == "active":
                # Cromagnon : attack2 = lancer de lance (projectile, pas de hitbox mêlée)
                # Samourai  : attack2 = shuriken (projectile, pas de hitbox mêlée)
                # Robot     : explosion au sol (animation + hitbox large)
                # Chevalier : ruée — déplacement forcé vers l'avant + hitbox
                if self.name == "Cromagnon" and self.attack2_frame == 1:
                    self.wants_to_shoot = True
                elif self.name == "Samourai" and self.attack2_frame == 1:
                    self.wants_to_shoot2 = True
                elif self.name == "Robot":
                    if self.attack2_frame == 1:
                        self.wants_to_explode = True
                    self.attack2_hitbox_active = True
                elif self.name == "Chevalier":
                    self.attack2_hitbox_active = True
                    rush_speed = int(self.speed * 2.2)
                    new_x = self.x + (rush_speed if self.facing_right else -rush_speed)
                    self.x = max(0, min(1280 - self.width, new_x))
                if self.attack2_frame >= self.attack2_active:
                    self.attack2_phase = "recovery"
                    self.attack2_frame = 0

            elif self.attack2_phase == "recovery":
                if self.attack2_frame >= self.attack2_recovery:
                    self.attack2_phase = None
                    self.attack2_frame = 0

        self.attack2_input_prev = attack2_pressed

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

        # --- Saut (simple + double saut) ---
        jump_pressed = self.inputs.get("jump", False)
        # Front montant uniquement — évite de consommer les deux sauts d'un seul appui maintenu
        if jump_pressed and not self.jump_prev:
            if self.on_ground and self.attack_phase != "recovery":
                # Premier saut depuis le sol
                self.velocity_y      = self.jump_strength
                self.on_ground       = False
                self.jumps_remaining = 1   # il reste 1 saut (le double)
            elif self.jumps_remaining > 0 and not self.on_ground:
                # Double saut en l'air — légèrement moins puissant
                self.velocity_y      = int(self.jump_strength * 0.85)
                self.jumps_remaining = 0
        self.jump_prev = jump_pressed

        # --- Timer animation ---
        self.anim_timer += 1
        if self.anim_timer >= self.anim_interval:
            self.anim_timer = 0

        self.apply_gravity()

        # --- Regard automatique ---
        # On se tourne vers l'adversaire seulement si on n'est pas en pleine attaque
        if not self.is_attacking and self.opponent and self.opponent.is_alive and self.is_alive:
            self.facing_right = self.opponent.x > self.x

    def apply_gravity(self):
        self.velocity_y += self.gravity
        self.y += self.velocity_y

    # ------------------------------------------------------------------ #
    #  RENDU
    # ------------------------------------------------------------------ #

    def render(self, RenderEngine):
        if self.sprite_idle:
            floor_y = getattr(self, "floor_y", 620)
            hb = self.hitbox
            dist_to_floor = max(0, floor_y - hb.bottom)
            shadow_w = max(10, int(hb.width * (1.0 - min(1.0, dist_to_floor / 300.0))))
            shadow_h = 10
            
            shadow_surf = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
            pygame.draw.ellipse(shadow_surf, (0, 0, 0, 150), (0, 0, shadow_w, shadow_h))
            
            RenderEngine.internal_surface.blit(shadow_surf, (hb.centerx - shadow_w // 2, floor_y - shadow_h // 2))

            # Choix du sprite (priorité : hit > attaque2 > attaque1 > saut > marche/dash > idle)
            if self.hit_stun > 0:
                image_to_draw = self.sprite_hit
            elif self.attack2_phase is not None:
                image_to_draw = self.sprite_attack2
            elif self.is_attacking:
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

            # Debug hitbox physique (verte)
            #pygame.draw.rect(RenderEngine.internal_surface, (0, 255, 0), self.hitbox, 2)

            # Debug hitbox attaque (rouge)
            #if self.attack_hitbox:
                #pygame.draw.rect(RenderEngine.internal_surface, (255, 0, 0), self.attack_hitbox, 2)

            # Debug hitbox bouclier (bleue)
            #if self.shield_hitbox:
                #pygame.draw.rect(RenderEngine.internal_surface, (100, 180, 255), self.shield_hitbox, 2)

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
        if keys.get("right", False) and self.x < 1280 - self.width:
            self.x += self.speed

    def reconcile(self, server_x, server_y, ack_seq):
        # On ne modifie plus "facing_right" ici ! Le tick() s'en occupe.
        self.x = server_x
        self.y = server_y
        self.pending_inputs = [p for p in self.pending_inputs if p["seq"] > ack_seq]
        for pending in self.pending_inputs:
            self.apply_movement_only(pending["inputs"])