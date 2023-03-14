import time

from PlayerState import PlayerStateBase
from Helper import Actions


class StateStaff(PlayerStateBase):
    # update the player statistics
    def update(self, pos_self, pos_opponent, action_self, action_opponent, action_opponent_is_valid):
        self.action = action_self

        # check if the shield has to reduced
        if self.shield_time > 0:
            self.shield_time = max(self.shield_max_time-(time.time()-self.shield_start_time), 0)

        # check if shield is active
        if self.shield_time > 0:
            if action_self == Actions.shield:
                # invalid
                pass
            self.shield_time = max(self.shield_max_time-(time.time()-self.shield_start_time), 0)
        elif action_self == Actions.shield:
            if self.num_shield > 0:
                self.num_shield        -= 1
                self.shield_time        = self.shield_max_time
                self.shield_health      = self.shield_health_max
                self.shield_start_time  = time.time()

        # update shield HP
        if self.shield_time <= 0:
            self.shield_health = 0

        # check for harm
        if action_opponent_is_valid:
            if pos_self == 4 and pos_opponent != 4:
                # we are protected from harm
                pass
            elif pos_self != 4 and pos_opponent == 4:
                # we are protected from harm
                pass
            else:
                hp_reduction = 0
                if action_opponent == Actions.shoot:
                    hp_reduction = self.bullet_hp
                elif action_opponent == Actions.grenade:
                    hp_reduction = self.grenade_hp
                if self.shield_time > 0:
                    if self.shield_health > 0:
                        self.shield_health -= hp_reduction
                    if self.shield_health < 0:
                        # we loose health
                        hp_reduction = -1*self.shield_health
                        self.shield_health = 0
                    else:
                        hp_reduction = 0
                # change the health
                self.hp -= hp_reduction
                if self.hp <= 0:
                    # we are dead
                    self.hp = self.max_hp
                    self.num_deaths += 1
                    self.hp         = self.max_hp
                    self.action     = action_self
                    self.bullets    = self.magazine_size
                    self.grenades   = self.max_grenades
                    self.shield_time = 0
                    self.shield_health = 0
                    self.num_shield = self.max_shields

        # check for reduction in ammo
        if action_self == Actions.shoot:
            self.bullets = max(0, self.bullets-1)

        if action_self == Actions.grenade:
            self.grenades = max(0, self.grenades-1)

        if action_self == Actions.reload:
            if self.bullets > 0:
                # invalid
                pass
            else:
                self.bullets = self.magazine_size

    def action_is_valid(self, action_self):
        ret = True
        # check if the shield has to reduced
        if action_self == Actions.shield:
            if self.shield_time > 0:
                # invalid
                ret = False
        elif action_self == Actions.shoot:
            if self.bullets <= 0:
                # invalid
                ret = False

        elif action_self == Actions.grenade:
            if self.grenades <= 0:
                # invalid
                ret = False

        elif action_self == Actions.reload:
            if self.bullets > 0:
                # invalid
                ret = False

        return ret
