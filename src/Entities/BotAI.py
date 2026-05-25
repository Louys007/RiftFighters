"""
BotAI.py — RiftFighters
=======================
IA par personnage + par difficulté.

Personnages :
  Cromagnon — mêlée, lance (attack2) si dist > 220px
  Samourai  — mêlée rapide, shuriken (attack2) entre 160-420px
  Robot     — reste à distance, tir (attack1), explosion (attack2) si trop proche
  Chevalier — mêlée, ruée (attack2) à distance moyenne pour surprendre

Difficulté :
  EASY   — avance droit, attack1 only, pas de bouclier/dash
  NORMAL — bouclier sur projectile, dash, attack2 situationnelle
  HARD   — feintes, dash agressif, punit les recoveries, bouclier réactif
"""

import random

PROFILES = {
    "EASY": {
        "reaction":       28,
        "noise":          0.32,
        "use_atk2":       False,
        "use_shield":     False,
        "use_dash":       False,
        "punish":         False,
        "feint":          0.00,
        "shield_on_proj": False,
        "aggro":          0.90,
        "double_jump":    False,
    },
    "NORMAL": {
        "reaction":       12,
        "noise":          0.07,
        "use_atk2":       True,
        "use_shield":     True,
        "use_dash":       True,
        "punish":         True,
        "feint":          0.08,
        "shield_on_proj": True,
        "aggro":          0.72,
        "double_jump":    True,
    },
    "HARD": {
        "reaction":       3,
        "noise":          0.01,
        "use_atk2":       True,
        "use_shield":     True,
        "use_dash":       True,
        "punish":         True,
        "feint":          0.20,
        "shield_on_proj": True,
        "aggro":          0.58,
        "double_jump":    True,
    },
}

MELEE_ATK_RANGE = 185
MELEE_TOO_CLOSE = 80
ROBOT_MIN       = 290
ROBOT_MAX       = 570
ROBOT_DANGER    = 160
RUSH_RANGE      = 380   # Chevalier : déclenche la ruée sous cette distance

S_APPROACH   = "approach"
S_ATTACK     = "attack"
S_RETREAT    = "retreat"
S_SHIELD     = "shield"
S_FEINT      = "feint"
S_REPOSITION = "reposition"


def _n():
    return {"left": False, "right": False, "jump": False,
            "attack": False, "attack2": False, "shield": False}


class BotAI:
    def __init__(self, bot_player, difficulty="NORMAL"):
        self.bot    = bot_player
        self.diff   = difficulty.upper()
        self.p      = PROFILES.get(self.diff, PROFILES["NORMAL"])
        self.name   = bot_player.name
        self.ranged = (self.name == "Robot")

        self._state       = S_APPROACH
        self._state_timer = 0
        self._react_timer = 0
        self._next_state  = None

        self._atk_cd    = 0
        self._jump_cd   = 0
        self._shield_cd = 0
        self._dash_cd   = 0

        self._dash_seq  = []
        self._dash_key  = ""

        self._in_air_prev    = False
        self._double_jump_cd = 0

        self._prev = _n()

    # ------------------------------------------------------------------ #
    #  API
    # ------------------------------------------------------------------ #

    def tick(self, opponent) -> dict:
        me = self.bot
        p  = self.p

        self._atk_cd         = max(0, self._atk_cd         - 1)
        self._jump_cd        = max(0, self._jump_cd        - 1)
        self._shield_cd      = max(0, self._shield_cd      - 1)
        self._dash_cd        = max(0, self._dash_cd        - 1)
        self._double_jump_cd = max(0, self._double_jump_cd - 1)

        if random.random() < p["noise"]:
            return self._prev

        dx   = opponent.hitbox.centerx - me.hitbox.centerx
        dist = abs(dx)
        go_r = dx > 0

        me_busy      = me.is_stunned or me.is_attacking
        opp_recovery = opponent.is_in_recovery
        opp_proj     = self._opp_shooting(opponent)

        # Dash en cours
        if self._dash_seq:
            inputs = _n()
            inputs[self._dash_key] = self._dash_seq.pop(0)
            self._prev = inputs
            return inputs

        # Décision
        if self._react_timer > 0:
            self._react_timer -= 1
            if self._react_timer == 0 and self._next_state:
                self._state       = self._next_state
                self._next_state  = None
                self._state_timer = 0
        else:
            if   self.name == "Robot":
                self._decide_robot(dist, opp_recovery, opp_proj, me_busy)
            elif self.name == "Cromagnon":
                self._decide_cromagnon(dist, opp_recovery, opp_proj, me_busy)
            elif self.name == "Samourai":
                self._decide_samourai(dist, opp_recovery, opp_proj, me_busy)
            elif self.name == "Chevalier":
                self._decide_chevalier(dist, opp_recovery, opp_proj, me_busy)

        self._state_timer += 1
        inputs = self._run_state(opponent, dist, dx, go_r, opp_recovery)

        if p["double_jump"]:
            self._try_double_jump(inputs, me)

        self._prev = inputs
        return inputs

    # ------------------------------------------------------------------ #
    #  DOUBLE SAUT
    # ------------------------------------------------------------------ #

    def _try_double_jump(self, inputs, me):
        just_left_ground = (not me.on_ground) and not self._in_air_prev
        self._in_air_prev = not me.on_ground
        if just_left_ground:
            self._double_jump_cd = 8
        if (not me.on_ground and me.jumps_remaining > 0
                and self._double_jump_cd == 0
                and not inputs.get("jump", False)):
            inputs["jump"]        = True
            self._double_jump_cd  = 40

    # ------------------------------------------------------------------ #
    #  DÉTECTION PROJECTILE ADVERSE
    # ------------------------------------------------------------------ #

    def _opp_shooting(self, opponent) -> bool:
        if opponent.name in ("Robot", "Cromagnon"):
            if opponent.attack_phase == "active" and opponent.attack_frame <= 3:
                return True
            if opponent.attack2_phase == "active" and opponent.attack2_frame <= 3:
                return True
        if opponent.name == "Samourai":
            if opponent.attack2_phase == "active" and opponent.attack2_frame <= 3:
                return True
        return False

    # ------------------------------------------------------------------ #
    #  DÉCISIONS PAR PERSONNAGE
    # ------------------------------------------------------------------ #

    def _decide_cromagnon(self, dist, opp_recovery, opp_proj, me_busy):
        p = self.p; new = None
        if p["shield_on_proj"] and opp_proj and self._shield_cd == 0 and not me_busy:
            new = S_SHIELD
        elif p["punish"] and opp_recovery and not me_busy:
            new = S_ATTACK
        elif dist < MELEE_ATK_RANGE and not me_busy:
            new = S_RETREAT if dist < MELEE_TOO_CLOSE else (
                  S_ATTACK if random.random() < p["aggro"] else S_RETREAT)
        else:
            if p["feint"] > 0 and dist < MELEE_ATK_RANGE + 100 and random.random() < p["feint"]:
                new = S_FEINT
            else:
                new = S_APPROACH
        self._go(new)

    def _decide_samourai(self, dist, opp_recovery, opp_proj, me_busy):
        p = self.p; new = None
        if p["shield_on_proj"] and opp_proj and self._shield_cd == 0 and not me_busy:
            new = S_SHIELD
        elif p["punish"] and opp_recovery and not me_busy:
            new = S_ATTACK
        elif dist < MELEE_ATK_RANGE and not me_busy:
            if dist < MELEE_TOO_CLOSE:
                new = S_RETREAT
            elif random.random() < p["aggro"]:
                new = S_ATTACK
            else:
                new = S_FEINT if random.random() < p["feint"] else S_RETREAT
        else:
            # Shuriken depuis distance moyenne
            if p["use_atk2"] and dist < 420 and not me_busy and self._atk_cd == 0:
                new = S_ATTACK
            else:
                new = S_APPROACH
        self._go(new)

    def _decide_chevalier(self, dist, opp_recovery, opp_proj, me_busy):
        """Mêlée + ruée (attack2) pour couvrir la distance rapidement."""
        p = self.p; new = None
        if p["shield_on_proj"] and opp_proj and self._shield_cd == 0 and not me_busy:
            new = S_SHIELD
        elif p["punish"] and opp_recovery and not me_busy:
            new = S_ATTACK
        elif dist < MELEE_ATK_RANGE and not me_busy:
            if dist < MELEE_TOO_CLOSE:
                new = S_RETREAT
            elif random.random() < p["aggro"]:
                new = S_ATTACK
            else:
                new = S_FEINT if random.random() < p["feint"] else S_RETREAT
        else:
            # Dans la portée de ruée : attack2 pour bondir sur l'adversaire
            if p["use_atk2"] and MELEE_ATK_RANGE <= dist <= RUSH_RANGE and not me_busy and self._atk_cd == 0:
                new = S_ATTACK
            elif p["use_dash"] and dist > 360 and self._dash_cd == 0 and random.random() < 0.14:
                new = S_APPROACH
            else:
                new = S_APPROACH
        self._go(new)

    def _decide_robot(self, dist, opp_recovery, opp_proj, me_busy):
        p = self.p; new = None
        if dist < ROBOT_DANGER:
            new = S_ATTACK
        elif opp_proj and p["use_shield"] and self._shield_cd == 0 and not me_busy:
            new = S_SHIELD
        elif p["punish"] and opp_recovery and dist < ROBOT_MAX and not me_busy:
            new = S_ATTACK
        elif ROBOT_MIN <= dist <= ROBOT_MAX and not me_busy:
            new = S_ATTACK
        elif dist < ROBOT_MIN:
            new = S_REPOSITION
        else:
            new = S_APPROACH
        self._go(new)

    def _go(self, new):
        if new and new != self._state:
            self._next_state  = new
            self._react_timer = self.p["reaction"]

    # ------------------------------------------------------------------ #
    #  EXÉCUTION
    # ------------------------------------------------------------------ #

    def _run_state(self, opponent, dist, dx, go_r, opp_recovery) -> dict:
        inputs = _n()
        me = self.bot
        p  = self.p

        if self._state == S_APPROACH:
            inputs["right" if go_r else "left"] = True
            if p["use_dash"] and dist > 360 and self._dash_cd == 0:
                if random.random() < 0.12:
                    self._start_dash(go_r)
                    self._dash_cd = 38
            if self._should_jump(opponent):
                inputs["jump"] = True; self._jump_cd = 24

        elif self._state == S_ATTACK:
            self._do_attack(inputs, dist, me, p, go_r)

        elif self._state == S_RETREAT:
            inputs["left" if go_r else "right"] = True
            if p["use_dash"] and dist < MELEE_TOO_CLOSE + 30 and self._dash_cd == 0:
                if self.name == "Samourai":
                    self._start_dash(not go_r); self._dash_cd = 38
            if self._state_timer > 22:
                self._state = S_APPROACH; self._state_timer = 0

        elif self._state == S_SHIELD:
            inputs["shield"] = True
            if self._state_timer >= random.randint(8, 15):
                inputs["shield"] = False
                self._shield_cd  = 42
                self._state      = S_APPROACH; self._state_timer = 0

        elif self._state == S_FEINT:
            if self._state_timer < 7:
                inputs["right" if go_r else "left"] = True
            else:
                inputs["left" if go_r else "right"] = True
            if self._state_timer >= 16:
                self._state = S_ATTACK; self._state_timer = 0

        elif self._state == S_REPOSITION:
            inputs["right" if (not go_r) else "left"] = True
            if dist >= ROBOT_MIN:
                self._state = S_ATTACK; self._state_timer = 0

        # Saut spontané mêlée
        if not self.ranged and me.on_ground and self._jump_cd == 0 and dist < 140:
            if random.random() < 0.025:
                inputs["jump"] = True; self._jump_cd = 30

        return inputs

    # ------------------------------------------------------------------ #
    #  CHOIX D'ATTAQUE PAR PERSONNAGE
    # ------------------------------------------------------------------ #

    def _do_attack(self, inputs, dist, me, p, go_r):
        if me.is_attacking or me.is_stunned or self._atk_cd > 0:
            if not self.ranged and dist > 55:
                inputs["right" if go_r else "left"] = True
            return

        use2 = False
        if p["use_atk2"]:
            if self.name == "Cromagnon":
                use2 = dist > 220

            elif self.name == "Samourai":
                use2 = 160 < dist < 420 and random.random() < 0.55

            elif self.name == "Chevalier":
                # Ruée si adversaire entre portée mêlée et portée de ruée
                use2 = MELEE_ATK_RANGE <= dist <= RUSH_RANGE

            elif self.name == "Robot":
                use2 = dist < ROBOT_DANGER + 50

        if use2:
            inputs["attack2"] = True
            self._atk_cd = me.attack2_startup + me.attack2_active + me.attack2_recovery + 10
        else:
            inputs["attack"] = True
            self._atk_cd = me.attack_startup + me.attack_active + me.attack_recovery + 8

        if not self.ranged and dist > 60:
            inputs["right" if go_r else "left"] = True

    # ------------------------------------------------------------------ #
    #  DASH
    # ------------------------------------------------------------------ #

    def _start_dash(self, go_right: bool):
        self._dash_key = "right" if go_right else "left"
        self._dash_seq = [True, False, True, False]

    def _should_jump(self, opponent) -> bool:
        me = self.bot
        if self._jump_cd > 0 or not me.on_ground:
            return False
        return opponent.y < me.y - 100