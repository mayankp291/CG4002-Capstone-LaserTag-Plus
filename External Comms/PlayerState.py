import time
from abc import abstractmethod


class Player():
    def __init__(self):
        self.max_grenades       = 2
        self.max_shields        = 3
        self.bullet_hp          = 10
        self.grenade_hp         = 30
        self.shield_max_time    = 10
        self.shield_health_max  = 30
        self.magazine_size      = 6
        self.max_hp             = 100

        self.hp             = self.max_hp
        self.action         = 'none'
        self.bullets        = self.magazine_size
        self.grenades       = self.max_grenades
        self.shield_time    = 0
        self.shield_health  = 0
        self.num_shield     = self.max_shields
        self.num_deaths     = 0

        self.shield_is_active = False
        self.curr_time = time.time()
        self.prev_time = time.time()
        self.shield_timeout = False
        
        self.state = self.get_dict()

    def get_dict (self):
        _player = dict()
        _player['hp']               = self.hp
        _player['action']           = self.action
        _player['bullets']          = self.bullets
        _player['grenades']         = self.grenades
        _player['shield_time']      = self.shield_time
        _player['shield_health']    = self.shield_health
        _player['num_deaths']       = self.num_deaths
        _player['num_shield']       = self.num_shield
        return _player

    def initialize(self, action, bullets_remaining, grenades_remaining,
                   hp, num_deaths, num_unused_shield,
                   shield_health, shield_time_remaining):
        self.hp             = hp
        self.action         = action
        self.bullets        = bullets_remaining
        self.grenades       = grenades_remaining
        self.shield_time    = shield_time_remaining
        self.shield_health  = shield_health
        self.num_shield     = num_unused_shield
        self.num_deaths     = num_deaths


    def initialize_from_dict(self, player_dict: dict):
        self.hp             = int(player_dict['hp'])
        self.action         = player_dict['action']
        self.bullets        = int(player_dict['bullets'])
        self.grenades       = int(player_dict['grenades'])
        self.shield_time    = float(player_dict['shield_time'])
        self.shield_health  = int(player_dict['shield_health'])
        self.num_shield     = int(player_dict['num_shield'])
        self.num_deaths     = int(player_dict['num_deaths'])
        if self.action == 'shield':
            self.shield_is_active = True
            # self.curr_time = time.time()

    def initialize_from_player_state(self, player_state):
        self.hp             = player_state.hp
        self.action         = player_state.action
        self.bullets        = player_state.bullets_remaining
        self.grenades       = player_state.grenades_remaining
        self.shield_time    = player_state.shield_time_remaining
        self.shield_health  = player_state.shield_health
        self.num_shield     = player_state.num_unused_shield
        self.num_deaths     = player_state.num_deaths

    @abstractmethod
    def update(self, pos_self, pos_opponent, action_self,
               action_opponent, action_opponent_is_valid):
        ...

    @abstractmethod
    def action_is_valid(self, action_self):
        ...
    
    def respawn(self):
        self.hp = self.max_hp
        self.bullets = self.magazine_size
        self.grenades = self.max_grenades
        self.shield_time = 0
        self.shield_health = 0
        self.num_shield = self.max_shields
        self.num_deaths += 1
        self.shield_is_active = False
    
    def shoot(self):
        self.action = 'shoot'
        
        if self.bullets > 0:
            self.bullets -= 1
        
        self.state = self.get_dict()

    def reload(self):
        self.action = 'reload'
        if self.bullets <= 0:
            self.bullets = self.magazine_size
        self.state = self.get_dict()
    
    def grenade(self):
        self.action = 'grenade'
        if self.grenades > 0:
            self.grenades -= 1
        self.state = self.get_dict()

    def shield(self):
        self.action = 'shield'
        if self.num_shield > 0 and not self.shield_is_active and self.shield_time == 0:
            self.num_shield -= 1
            self.shield_is_active = True
            self.shield_health = self.shield_health_max
            self.shield_time = self.shield_max_time
            self.shield_timeout = False
            self.curr_time = time.time()
        self.state = self.get_dict()

    def shoot_hit(self):
        # Shield is active
        if self.shield_is_active:
            # self.shield_health -= self.bullet_hp
            # destroy shield
            if self.shield_health <= self.bullet_hp:
                self.shield_is_active = False
                self.shield_health = 0
                self.shield_time = 0
            # Does not destroy shield
            else:
                self.shield_health -= self.bullet_hp
        # Shield is not active
        else:
            self.hp -= self.bullet_hp
            if self.hp <= 0:
                self.respawn()
        
        self.state = self.get_dict()
    
    def grenade_hit(self):
        # Shield is active
        if self.shield_is_active:
            # self.shield_health -= self.grenade_hp
            # destroy shield 
            if self.shield_health == self.shield_health_max:
                self.shield_is_active = False
                self.shield_health = 0
                self.shield_time = 0
            # Destroy shield and damage player
            else:
                self.shield_is_active = False
                # shield takes some damage
                damage = self.grenade_hp - self.shield_health
                self.shield_health = 0
                self.shield_time = 0

                # rest on player
                self.hp -= damage

                if self.hp <= 0:
                    self.respawn()

        # Shield is not active
        else:
            self.hp -= self.grenade_hp
            if self.hp <= 0:
                self.respawn()
        
        self.state = self.get_dict()
    
    def logout(self):
        self.action = 'logout'
        self.state = self.get_dict()

    def update_state(self):
        self.state = self.get_dict()

    def update_shield_time(self):
        # TODO check this
        # if self.shield_is_active:
        self.prev_time = self.curr_time
        self.curr_time = time.time()
        diff = self.curr_time - self.prev_time
        
        if not self.shield_is_active and self.shield_time == 0:
            return

        self.shield_time -= diff

        if self.shield_time <= 0:
            self.shield_is_active = False
            self.shield_health = 0
            self.shield_time = 0
            self.shield_timeout = True
            self.state = self.get_dict()
        
        self.state = self.get_dict()

    ### TODO check this
    def sync_eval(self, state):
        self.initialize_from_dict(state)
