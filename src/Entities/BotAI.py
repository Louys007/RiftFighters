"""
BotAI.py — RiftFighters
=======================
IMPORTANT : Player.py détecte les FRONTS MONTANTS (False→True) pour :
  - attack / attack2  (attack_input_prev)
  - jump              (jump_prev)
  - dash              (_update_double_tap : left_prev / right_prev)

Le bot doit donc envoyer True UNE SEULE frame puis False pour déclencher
ces actions. Les inputs continus (bouclier, déplacement) fonctionnent normalement.

Comportement par personnage :
  Cromagnon — mêlée (attack1) si dist < 220px, lance (attack2) si dist > 220px
  Samourai  — mêlée (attack1) si dist < 160px, shuriken (attack2) entre 160-420px
  Robot     — tir (attack1) dans zone 290-570px, explosion (attack2) si dist < 210px
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

        # Dash : séquence de fronts montants à envoyer
        self._dash_seq = []
        self._dash_key = ""

        # Suivi des fronts montants BOT (pour ne pas renvoyer True en continu)
        self._atk_sent   = False   # True si on a déjà envoyé attack=True ce cycle
        self._atk2_sent  = False
        self._jump_sent  = False

        # Double saut : état interne
        self._in_air_prev    = False   # était-on en l'air la frame précédente ?
        self._double_jump_cd = 0       # délai avant de tenter le double saut

        self._prev = _n()

    # ------------------------------------------------------------------ #
    #  POINT D'ENTRÉE
    # ------------------------------------------------------------------ #

    def tick(self, opponent) -> dict:
        me = self.bot
        p  = self.p

        self._atk_cd        = max(0, self._atk_cd        - 1)
        self._jump_cd       = max(0, self._jump_cd       - 1)
        self._shield_cd     = max(0, self._shield_cd     - 1)
        self._dash_cd       = max(0, self._dash_cd       - 1)
        self._double_jump_cd = max(0, self._double_jump_cd - 1)

        if random.random() < p["noise"]:
            return self._prev

        dx   = opponent.hitbox.centerx - me.hitbox.centerx
        dist = abs(dx)
        go_r = dx > 0

        me_busy      = me.is_stunned or me.is_attacking
        opp_recovery = opponent.is_in_recovery
        opp_proj     = self._opp_shooting(opponent)

        # Dash en cours : priorité absolue
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
            if self.ranged:
                self._decide_robot(dist, opp_recovery, opp_proj, me_busy)
            elif self.name == "Cromagnon":
                self._decide_cromagnon(dist, opp_recovery, opp_proj, me_busy)
            else:
                self._decide_samourai(dist, opp_recovery, opp_proj, me_busy)

        self._state_timer += 1
        inputs = self._run_state(opponent, dist, dx, go_r, opp_recovery)

        # Double saut en l'air
        if p["double_jump"]:
            self._try_double_jump(inputs, me, opponent)

        self._prev = inputs
        return inputs

    # ------------------------------------------------------------------ #
    #  DOUBLE SAUT
    # ------------------------------------------------------------------ #

    def _try_double_jump(self, inputs, me, opponent):
        """
        Tente un double saut si on est en l'air et qu'il reste un saut.
        Envoie jump=True UNE SEULE frame (front montant), puis attend.
        """
        just_left_ground = (not me.on_ground) and self._in_air_prev == False
        self._in_air_prev = not me.on_ground

        if just_left_ground:
            # On vient de décoller : reset le cooldown du double saut
            self._double_jump_cd = 8   # attend 8 frames avant de tenter le double

        if (not me.on_ground
                and me.jumps_remaining > 0
                and self._double_jump_cd == 0
                and not inputs.get("jump", False)):
            # Envoie un front montant unique
            inputs["jump"]        = True
            self._double_jump_cd  = 40   # empêche un troisième saut fantôme

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
            if dist < MELEE_TOO_CLOSE:
                new = S_RETREAT
            elif random.random() < p["aggro"]:
                new = S_ATTACK
            else:
                new = S_RETREAT
        elif dist >= MELEE_ATK_RANGE:
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
        elif dist >= MELEE_ATK_RANGE:
            if p["use_atk2"] and dist < 420 and not me_busy and self._atk_cd == 0:
                new = S_ATTACK
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
                inputs["jump"] = True
                self._jump_cd  = 24

        elif self._state == S_ATTACK:
            self._do_attack(inputs, dist, me, p, go_r)

        elif self._state == S_RETREAT:
            inputs["left" if go_r else "right"] = True
            if p["use_dash"] and dist < MELEE_TOO_CLOSE + 30 and self._dash_cd == 0:
                if self.name == "Samourai":
                    self._start_dash(not go_r)
                    self._dash_cd = 38
            if self._state_timer > 22:
                self._state = S_APPROACH
                self._state_timer = 0

        elif self._state == S_SHIELD:
            inputs["shield"] = True
            if self._state_timer >= random.randint(8, 15):
                inputs["shield"]  = False
                self._shield_cd   = 42
                self._state       = S_APPROACH
                self._state_timer = 0

        elif self._state == S_FEINT:
            if self._state_timer < 7:
                inputs["right" if go_r else "left"] = True
            else:
                inputs["left" if go_r else "right"] = True
            if self._state_timer >= 16:
                self._state = S_ATTACK
                self._state_timer = 0

        elif self._state == S_REPOSITION:
            inputs["right" if (not go_r) else "left"] = True
            if dist >= ROBOT_MIN:
                self._state = S_ATTACK
                self._state_timer = 0

        # Saut spontané mêlée
        if not self.ranged and me.on_ground and self._jump_cd == 0 and dist < 140:
            if random.random() < 0.025:
                inputs["jump"] = True
                self._jump_cd  = 30

        return inputs

    # ------------------------------------------------------------------ #
    #  CHOIX D'ATTAQUE — FRONT MONTANT GARANTI
    # ------------------------------------------------------------------ #

    def _do_attack(self, inputs, dist, me, p, go_r):
        """
        Envoie attack ou attack2 en front montant :
        on n'envoie True que si le Player n'est pas déjà en train d'attaquer
        ET qu'on n'a pas déjà envoyé l'input ce cycle.
        """
        if me.is_attacking or me.is_stunned:
            if not self.ranged and dist > 55:
                inputs["right" if go_r else "left"] = True
            return

        if self._atk_cd > 0:
            if not self.ranged and dist > 55:
                inputs["right" if go_r else "left"] = True
            return

        # Choix attack1 vs attack2 selon perso et distance
        use2 = False
        if p["use_atk2"]:
            if self.name == "Cromagnon":
                use2 = dist > 220
            elif self.name == "Samourai":
                use2 = 160 < dist < 420 and random.random() < 0.55
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
    #  DASH — SÉQUENCE DE FRONTS MONTANTS
    # ------------------------------------------------------------------ #

    def _start_dash(self, go_right: bool):
        """
        Génère la séquence correcte pour déclencher _update_double_tap :
        True, False, True, False = 2 fronts montants dans la fenêtre de 15f.
        """
        self._dash_key = "right" if go_right else "left"
        self._dash_seq = [True, False, True, False]

    # ------------------------------------------------------------------ #
    #  HELPERS
    # ------------------------------------------------------------------ #

    def _should_jump(self, opponent) -> bool:
        me = self.bot
        if self._jump_cd > 0 or not me.on_ground:
            return False
        return opponent.y < me.y - 100

# -----------------------------------------------------------------------
# Profils
# -----------------------------------------------------------------------
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
    },
}

# Seuils de distance
MELEE_ATK_RANGE  = 185   # portée d'attaque mêlée
MELEE_TOO_CLOSE  = 80    # trop collé → recule ou dash arrière
ROBOT_MIN        = 290   # Robot : zone idéale minimum
ROBOT_MAX        = 570   # Robot : zone idéale maximum
ROBOT_DANGER     = 160   # Robot : adversaire trop proche → explosion

# États
S_IDLE       = "idle"
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
        self.bot   = bot_player
        self.diff  = difficulty.upper()
        self.p     = PROFILES.get(self.diff, PROFILES["NORMAL"])
        self.name  = bot_player.name   # "Cromagnon", "Robot", "Samourai"
        self.ranged = (self.name == "Robot")

        self._state       = S_APPROACH
        self._state_timer = 0
        self._react_timer = 0
        self._next_state  = None

        # Cooldowns internes (frames)
        self._atk_cd    = 0
        self._jump_cd   = 0
        self._shield_cd = 0
        self._dash_cd   = 0

        # Dash : on simule 2 fronts montants sur la même direction
        # Séquence : [True, False, True, False] = 2 appuis détectés
        self._dash_seq     = []   # liste de bools restants à envoyer
        self._dash_key     = ""   # "left" ou "right"

        self._prev = _n()   # inputs de la frame précédente (pour logique interne)

    # ------------------------------------------------------------------ #
    #  POINT D'ENTRÉE
    # ------------------------------------------------------------------ #

    def tick(self, opponent) -> dict:
        me = self.bot
        p  = self.p

        self._atk_cd    = max(0, self._atk_cd    - 1)
        self._jump_cd   = max(0, self._jump_cd   - 1)
        self._shield_cd = max(0, self._shield_cd - 1)
        self._dash_cd   = max(0, self._dash_cd   - 1)

        # Bruit
        if random.random() < p["noise"]:
            return self._prev

        dx   = opponent.hitbox.centerx - me.hitbox.centerx
        dist = abs(dx)
        go_r = dx > 0

        me_busy      = me.is_stunned or me.is_attacking
        opp_recovery = opponent.is_in_recovery
        opp_proj     = self._opp_shooting(opponent)

        # --- Dash en cours : on envoie la séquence ---
        if self._dash_seq:
            inputs = _n()
            val = self._dash_seq.pop(0)
            inputs[self._dash_key] = val
            self._prev = inputs
            return inputs

        # Réaction différée
        if self._react_timer > 0:
            self._react_timer -= 1
            if self._react_timer == 0 and self._next_state:
                self._state       = self._next_state
                self._next_state  = None
                self._state_timer = 0
        else:
            if self.ranged:
                self._decide_robot(dist, opp_recovery, opp_proj, me_busy, opponent)
            elif self.name == "Cromagnon":
                self._decide_cromagnon(dist, opp_recovery, opp_proj, me_busy)
            else:
                self._decide_samourai(dist, opp_recovery, opp_proj, me_busy)

        self._state_timer += 1
        inputs = self._run_state(opponent, dist, dx, go_r, opp_recovery, opp_proj)
        self._prev = inputs
        return inputs

    # ------------------------------------------------------------------ #
    #  DÉTECTION PROJECTILE ADVERSE
    # ------------------------------------------------------------------ #

    def _opp_shooting(self, opponent) -> bool:
        """True si l'adversaire vient de lancer un projectile vers nous."""
        if opponent.name in ("Robot", "Cromagnon"):
            if opponent.attack_phase == "active" and opponent.attack_frame <= 3:
                return True
        if opponent.name in ("Samourai", "Cromagnon"):
            if opponent.attack2_phase == "active" and opponent.attack2_frame <= 3:
                return True
        return False

    # ------------------------------------------------------------------ #
    #  DÉCISIONS PAR PERSONNAGE
    # ------------------------------------------------------------------ #

    def _decide_cromagnon(self, dist, opp_recovery, opp_proj, me_busy):
        """Mêlée principale + lance à distance."""
        p   = self.p
        new = None

        if p["shield_on_proj"] and opp_proj and self._shield_cd == 0 and not me_busy:
            new = S_SHIELD
        elif p["punish"] and opp_recovery and not me_busy:
            # Lance si loin, corps-à-corps si proche
            new = S_ATTACK
        elif dist < MELEE_ATK_RANGE and not me_busy:
            if dist < MELEE_TOO_CLOSE:
                new = S_RETREAT
            elif random.random() < p["aggro"]:
                new = S_ATTACK
            else:
                new = S_RETREAT
        elif dist >= MELEE_ATK_RANGE:
            if p["use_dash"] and dist > 380 and self._dash_cd == 0 and random.random() < 0.15:
                new = S_APPROACH  # on dashera depuis _run_state
            elif p["feint"] > 0 and dist < MELEE_ATK_RANGE + 100 and random.random() < p["feint"]:
                new = S_FEINT
            else:
                new = S_APPROACH
        self._go(new)

    def _decide_samourai(self, dist, opp_recovery, opp_proj, me_busy):
        """Mêlée rapide + shuriken pour harceler."""
        p   = self.p
        new = None

        if p["shield_on_proj"] and opp_proj and self._shield_cd == 0 and not me_busy:
            new = S_SHIELD
        elif p["punish"] and opp_recovery and not me_busy:
            new = S_ATTACK
        elif dist < MELEE_ATK_RANGE and not me_busy:
            if dist < MELEE_TOO_CLOSE:
                # Dash arrière ou recule
                if p["use_dash"] and self._dash_cd == 0:
                    new = S_RETREAT   # dash arrière déclenché dans _run_state
                else:
                    new = S_RETREAT
            elif random.random() < p["aggro"]:
                new = S_ATTACK
            else:
                new = S_FEINT if random.random() < p["feint"] else S_RETREAT
        elif dist >= MELEE_ATK_RANGE:
            # Le Samourai peut harceler au shuriken depuis la distance
            if p["use_atk2"] and dist < 420 and not me_busy and self._atk_cd == 0:
                new = S_ATTACK   # _do_attack choisira shuriken à cette distance
            elif p["use_dash"] and dist > 300 and self._dash_cd == 0 and random.random() < 0.18:
                new = S_APPROACH
            else:
                new = S_APPROACH
        self._go(new)

    def _decide_robot(self, dist, opp_recovery, opp_proj, me_busy, opponent):
        """Maintient la distance, tire, explose si trop proche."""
        p   = self.p
        new = None

        if dist < ROBOT_DANGER:
            new = S_ATTACK   # _do_attack choisira explosion (attack2)
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
    #  EXÉCUTION DES ÉTATS
    # ------------------------------------------------------------------ #

    def _run_state(self, opponent, dist, dx, go_r, opp_recovery, opp_proj) -> dict:
        inputs = _n()
        me     = self.bot
        p      = self.p

        if self._state == S_APPROACH:
            inputs["right" if go_r else "left"] = True
            # Dash vers l'adversaire si loin
            if p["use_dash"] and dist > 360 and self._dash_cd == 0:
                if random.random() < 0.12:
                    self._start_dash(go_r)
                    self._dash_cd = 38
            if self._should_jump(opponent):
                inputs["jump"] = True
                self._jump_cd  = 24

        elif self._state == S_ATTACK:
            self._do_attack(inputs, dist, me, p, go_r)

        elif self._state == S_RETREAT:
            inputs["left" if go_r else "right"] = True
            # Dash arrière si Samourai et trop collé
            if p["use_dash"] and dist < MELEE_TOO_CLOSE + 30 and self._dash_cd == 0:
                if self.name == "Samourai":
                    self._start_dash(not go_r)
                    self._dash_cd = 38
            if self._state_timer > 22:
                self._state = S_APPROACH
                self._state_timer = 0

        elif self._state == S_SHIELD:
            inputs["shield"] = True
            # Relâche après 8-15f pour ne pas subir le stun de bouclier (30f)
            if self._state_timer >= random.randint(8, 15):
                inputs["shield"]  = False
                self._shield_cd   = 42
                self._state       = S_APPROACH
                self._state_timer = 0

        elif self._state == S_FEINT:
            # Phase 1 (0-7f) : avance vite
            # Phase 2 (7-16f) : recule brusquement
            # → l'adversaire attend un coup qui ne vient pas, on exploite sa reaction
            if self._state_timer < 7:
                inputs["right" if go_r else "left"] = True
            else:
                inputs["left" if go_r else "right"] = True
            if self._state_timer >= 16:
                self._state       = S_ATTACK
                self._state_timer = 0

        elif self._state == S_REPOSITION:
            # Robot : recule pour retrouver la zone idéale
            flee_r = not go_r
            inputs["right" if flee_r else "left"] = True
            if dist >= ROBOT_MIN:
                self._state       = S_ATTACK
                self._state_timer = 0

        # Saut spontané en mêlée pour passer par-dessus
        if not self.ranged and me.on_ground and self._jump_cd == 0 and dist < 140:
            if random.random() < 0.025:
                inputs["jump"] = True
                self._jump_cd  = 30

        return inputs

    # ------------------------------------------------------------------ #
    #  CHOIX D'ATTAQUE TACTIQUE PAR PERSONNAGE
    # ------------------------------------------------------------------ #

    def _do_attack(self, inputs, dist, me, p, go_r):
        if self._atk_cd > 0 or me.is_attacking or me.is_stunned:
            # Maintient la position pendant le cooldown
            if not self.ranged and dist > 55:
                inputs["right" if go_r else "left"] = True
            return

        use2 = False

        if p["use_atk2"]:
            if self.name == "Cromagnon":
                # Lance (attack2) si adversaire à plus de 220px
                # En dessous, attaque mêlée (attack1)
                use2 = dist > 220

            elif self.name == "Samourai":
                # Shuriken (attack2) si adversaire entre 160 et 420px
                # Mêlée (attack1) si trop proche ou si on veut varier
                if 160 < dist < 420:
                    use2 = random.random() < 0.55   # 55% shuriken à cette distance
                else:
                    use2 = False

            elif self.name == "Robot":
                # Explosion (attack2) si l'adversaire est dans la zone de danger
                # Sinon tir normal (attack1)
                use2 = dist < ROBOT_DANGER + 50

        if use2:
            inputs["attack2"] = True
            self._atk_cd = me.attack2_startup + me.attack2_active + me.attack2_recovery + 10
        else:
            inputs["attack"] = True
            self._atk_cd = me.attack_startup + me.attack_active + me.attack_recovery + 8

        # Mêlée : colle à l'adversaire pour frapper
        if not self.ranged and dist > 60:
            inputs["right" if go_r else "left"] = True

    # ------------------------------------------------------------------ #
    #  DASH — SIMULATION CORRECTE DU DOUBLE-TAP
    # ------------------------------------------------------------------ #

    def _start_dash(self, go_right: bool):
        """
        Simule un double-tap pour déclencher le dash dans Player.
        _update_double_tap détecte les fronts montants (False→True).
        Séquence envoyée sur 4 frames : True, False, True, False
        = 2 fronts montants dans la fenêtre de 15 frames → dash déclenché.
        """
        self._dash_key = "right" if go_right else "left"
        self._dash_seq = [True, False, True, False]

    # ------------------------------------------------------------------ #
    #  HELPERS
    # ------------------------------------------------------------------ #

    def _should_jump(self, opponent) -> bool:
        me = self.bot
        if self._jump_cd > 0 or not me.on_ground:
            return False
        return opponent.y < me.y - 100