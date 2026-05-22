"""
BotAI.py
========
Intelligence artificielle pour RiftFighters.
Produit un dict d'inputs identique à celui d'un joueur humain, à 30 Hz.

Trois niveaux de difficulté :
  EASY   — réactions lentes (25f), erreurs fréquentes, pas de bouclier, pas de dash
  NORMAL — réactions correctes (12f), attaque à portée, bloque parfois, dash rare
  HARD   — réactions rapides (4f), punit les recoveries, dash, double saut offensif

Stratégie adaptée au personnage :
  Cromagnon / Samourai — mêlée : s'approche et frappe
  Robot                — distance : maintient un couloir de tir, recule si trop proche
"""

import random

# -----------------------------------------------------------------------
# Profils de difficulté
# -----------------------------------------------------------------------
DIFFICULTY_PROFILES = {
    "EASY": {
        "reaction_frames":  25,
        "attack2_chance":   0.10,
        "shield_chance":    0.00,
        "dodge_chance":     0.05,
        "punish_recovery":  False,
        "jump_chance":      0.01,
        "dash_chance":      0.00,
        "noise":            0.28,
    },
    "NORMAL": {
        "reaction_frames":  12,
        "attack2_chance":   0.28,
        "shield_chance":    0.30,
        "dodge_chance":     0.15,
        "punish_recovery":  True,
        "jump_chance":      0.03,
        "dash_chance":      0.04,
        "noise":            0.10,
    },
    "HARD": {
        "reaction_frames":  4,
        "attack2_chance":   0.42,
        "shield_chance":    0.60,
        "dodge_chance":     0.18,
        "punish_recovery":  True,
        "jump_chance":      0.06,
        "dash_chance":      0.10,
        "noise":            0.02,
    },
}

# Distances pour les personnages mêlée
MELEE_ATTACK_RANGE  = 190   # distance pour déclencher l'attaque
MELEE_CHASE_RANGE   = 500   # distance à partir de laquelle on court

# Distances pour le Robot (distance)
ROBOT_IDEAL_MIN     = 300   # trop proche → recule
ROBOT_IDEAL_MAX     = 600   # trop loin   → avance légèrement
ROBOT_FIRE_RANGE    = 700   # portée de tir (projectile traverse l'écran entier mais on tire pas dans le vide)
ROBOT_TOO_CLOSE     = 180   # distance d'urgence → fuit et utilise attack2

MELEE_CHARACTERS = {"Cromagnon", "Samourai"}

STATE_APPROACH  = "approach"
STATE_ATTACK    = "attack"
STATE_RETREAT   = "retreat"
STATE_SHIELD    = "shield"
STATE_REPOSITION = "reposition"   # Robot : se remet à bonne distance
STATE_WAIT      = "wait"


def _neutral() -> dict:
    return {"left": False, "right": False, "jump": False,
            "attack": False, "attack2": False, "shield": False}


class BotAI:
    def __init__(self, bot_player, difficulty: str = "NORMAL"):
        self.bot        = bot_player
        self.difficulty = difficulty.upper()
        self.profile    = DIFFICULTY_PROFILES.get(self.difficulty, DIFFICULTY_PROFILES["NORMAL"])
        self.is_ranged  = bot_player.name == "Robot"

        self._state           = STATE_APPROACH
        self._state_timer     = 0
        self._reaction_timer  = 0
        self._pending_state   = None

        self._attack_cooldown = 0
        self._jump_cooldown   = 0
        self._shield_timer    = 0

        self._last_inputs = _neutral()

    # ------------------------------------------------------------------ #
    #  API
    # ------------------------------------------------------------------ #

    def tick(self, opponent) -> dict:
        p  = self.profile
        me = self.bot

        self._attack_cooldown = max(0, self._attack_cooldown - 1)
        self._jump_cooldown   = max(0, self._jump_cooldown   - 1)
        if self._shield_timer > 0:
            self._shield_timer -= 1

        if random.random() < p["noise"]:
            return self._last_inputs

        dx   = opponent.hitbox.centerx - me.hitbox.centerx
        dist = abs(dx)

        opp_attacking = opponent.is_attacking
        opp_recovery  = opponent.is_in_recovery
        me_busy       = me.is_stunned or me.is_attacking

        # Réaction différée
        if self._reaction_timer > 0:
            self._reaction_timer -= 1
            if self._reaction_timer == 0 and self._pending_state:
                self._state         = self._pending_state
                self._pending_state = None
                self._state_timer   = 0
        else:
            if self.is_ranged:
                self._decide_state_ranged(dist, opp_attacking, opp_recovery, me_busy)
            else:
                self._decide_state_melee(dist, opp_attacking, opp_recovery, me_busy)

        self._state_timer += 1

        if self.is_ranged:
            inputs = self._execute_ranged(opponent, dist, dx, opp_recovery)
        else:
            inputs = self._execute_melee(opponent, dist, dx, opp_recovery)

        self._last_inputs = inputs
        return inputs

    # ------------------------------------------------------------------ #
    #  DÉCISION MÊLÉE (Cromagnon / Samourai)
    # ------------------------------------------------------------------ #

    def _decide_state_melee(self, dist, opp_attacking, opp_recovery, me_busy):
        p = self.profile
        new_state = None

        if p["punish_recovery"] and opp_recovery and not me_busy:
            if dist < MELEE_ATTACK_RANGE + 80:
                new_state = STATE_ATTACK

        elif opp_attacking and not opp_recovery and dist < 230:
            if random.random() < p["shield_chance"] and not me_busy:
                new_state = STATE_SHIELD

        elif dist < MELEE_ATTACK_RANGE and not me_busy:
            if random.random() < (1.0 - p["dodge_chance"]):
                new_state = STATE_ATTACK
            else:
                new_state = STATE_RETREAT

        elif dist >= MELEE_ATTACK_RANGE:
            new_state = STATE_APPROACH

        self._transition(new_state)

    # ------------------------------------------------------------------ #
    #  DÉCISION DISTANCE (Robot)
    # ------------------------------------------------------------------ #

    def _decide_state_ranged(self, dist, opp_attacking, opp_recovery, me_busy):
        p = self.profile
        new_state = None

        # Urgence : adversaire trop collé → fuite prioritaire
        if dist < ROBOT_TOO_CLOSE:
            new_state = STATE_RETREAT

        # Bouclier si l'adversaire attaque et arrive sur nous
        elif opp_attacking and not opp_recovery and dist < 300:
            if random.random() < p["shield_chance"] and not me_busy:
                new_state = STATE_SHIELD

        # Punir une recovery si à portée de tir
        elif p["punish_recovery"] and opp_recovery and dist < ROBOT_FIRE_RANGE and not me_busy:
            new_state = STATE_ATTACK

        # Dans la zone idéale → tire
        elif ROBOT_IDEAL_MIN <= dist <= ROBOT_IDEAL_MAX and not me_busy:
            new_state = STATE_ATTACK

        # Trop proche (pas encore urgence) → recule pour retrouver la zone
        elif dist < ROBOT_IDEAL_MIN:
            new_state = STATE_REPOSITION

        # Trop loin → avance prudemment
        elif dist > ROBOT_IDEAL_MAX:
            new_state = STATE_APPROACH

        self._transition(new_state)

    def _transition(self, new_state):
        if new_state and new_state != self._state:
            self._pending_state  = new_state
            self._reaction_timer = self.profile["reaction_frames"]

    # ------------------------------------------------------------------ #
    #  EXÉCUTION MÊLÉE
    # ------------------------------------------------------------------ #

    def _execute_melee(self, opponent, dist, dx, opp_recovery) -> dict:
        inputs = _neutral()
        p      = self.profile
        me     = self.bot
        go_right = dx > 0

        if self._state == STATE_APPROACH:
            inputs["right" if go_right else "left"] = True
            if self._should_jump(opponent):
                inputs["jump"]      = True
                self._jump_cooldown = 22

        elif self._state == STATE_ATTACK:
            if dist > 55:
                inputs["right" if go_right else "left"] = True
            if self._attack_cooldown == 0 and not me.is_attacking and not me.is_stunned:
                if random.random() < p["attack2_chance"]:
                    inputs["attack2"]     = True
                    self._attack_cooldown = me.attack2_startup + me.attack2_active + me.attack2_recovery + 6
                else:
                    inputs["attack"]      = True
                    self._attack_cooldown = me.attack_startup + me.attack_active + me.attack_recovery + 6
            if self.difficulty == "HARD" and me.on_ground and dist < 260:
                if random.random() < 0.04 and self._jump_cooldown == 0:
                    inputs["jump"]      = True
                    self._jump_cooldown = 28

        elif self._state == STATE_RETREAT:
            inputs["left" if go_right else "right"] = True
            if self._state_timer > 18:
                self._state = STATE_APPROACH
                self._state_timer = 0

        elif self._state == STATE_SHIELD:
            if self._shield_timer == 0:
                self._shield_timer = random.randint(6, 12)
            inputs["shield"] = True
            if self._shield_timer <= 1:
                inputs["shield"]  = False
                self._state       = STATE_APPROACH
                self._state_timer = 0

        # Saut spontané pour franchir
        if me.on_ground and self._jump_cooldown == 0 and dist < 150:
            if random.random() < p["jump_chance"]:
                inputs["jump"]      = True
                self._jump_cooldown = 25

        return inputs

    # ------------------------------------------------------------------ #
    #  EXÉCUTION DISTANCE (Robot)
    # ------------------------------------------------------------------ #

    def _execute_ranged(self, opponent, dist, dx, opp_recovery) -> dict:
        inputs = _neutral()
        p      = self.profile
        me     = self.bot
        # Recule = direction opposée à l'adversaire
        go_right  = dx > 0
        flee_right = not go_right   # fuir = aller dans la direction opposée

        if self._state == STATE_APPROACH:
            # Avance prudemment vers la zone idéale
            inputs["right" if go_right else "left"] = True

        elif self._state == STATE_ATTACK:
            # Ne bouge pas pour viser — tire
            if self._attack_cooldown == 0 and not me.is_attacking and not me.is_stunned:
                # Robot préfère attack1 (projectile) sauf si vraiment trop proche
                if dist < ROBOT_TOO_CLOSE + 40 and random.random() < p["attack2_chance"]:
                    # Corps-à-corps d'urgence
                    inputs["attack2"]     = True
                    self._attack_cooldown = me.attack2_startup + me.attack2_active + me.attack2_recovery + 6
                else:
                    inputs["attack"]      = True
                    self._attack_cooldown = me.attack_startup + me.attack_active + me.attack_recovery + 8

            # Maintient une légère correction de position pendant la recovery
            if me.attack_phase == "recovery" or me.attack2_phase == "recovery":
                if dist < ROBOT_IDEAL_MIN:
                    inputs["right" if flee_right else "left"] = True

        elif self._state == STATE_RETREAT:
            # Fuite prioritaire — s'éloigne au max
            inputs["right" if flee_right else "left"] = True

            # Saute pour esquiver si l'adversaire est au sol
            if me.on_ground and opponent.on_ground and self._jump_cooldown == 0:
                if random.random() < 0.08:
                    inputs["jump"]      = True
                    self._jump_cooldown = 20

            if self._state_timer > 22 and dist > ROBOT_TOO_CLOSE:
                self._state       = STATE_REPOSITION
                self._state_timer = 0

        elif self._state == STATE_REPOSITION:
            # Recule pour retrouver la zone idéale
            inputs["right" if flee_right else "left"] = True
            if dist >= ROBOT_IDEAL_MIN:
                self._state       = STATE_ATTACK
                self._state_timer = 0

        elif self._state == STATE_SHIELD:
            if self._shield_timer == 0:
                self._shield_timer = random.randint(5, 10)
            inputs["shield"] = True
            if self._shield_timer <= 1:
                inputs["shield"]  = False
                self._state       = STATE_REPOSITION
                self._state_timer = 0

        # Saut spontané (esquive verticale)
        if me.on_ground and self._jump_cooldown == 0:
            if random.random() < p["jump_chance"]:
                inputs["jump"]      = True
                self._jump_cooldown = 25

        return inputs

    # ------------------------------------------------------------------ #
    #  HELPERS
    # ------------------------------------------------------------------ #

    def _should_jump(self, opponent) -> bool:
        me = self.bot
        if self._jump_cooldown > 0 or not me.on_ground:
            return False
        if opponent.y < me.y - 100:
            return True
        return False