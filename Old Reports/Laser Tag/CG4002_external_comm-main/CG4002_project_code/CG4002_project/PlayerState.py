import time
from abc import abstractmethod


class PlayerStateBase:
    def __init__(self):
        self.max_grenades       = 2
        self.max_shields        = 3
        self.bullet_hp          = 10
        self.grenade_hp         = 30
        self.shield_max_time    = 10
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

        self.shield_start_time = time.time()-30

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
        self.hp             = player_dict['hp']
        self.action         = player_dict['action']
        self.bullets        = player_dict['bullets']
        self.grenades       = player_dict['grenades']
        self.shield_time    = player_dict['shield_time']
        self.shield_health  = player_dict['shield_health']
        self.num_shield     = player_dict['num_shield']
        self.num_deaths     = player_dict['num_deaths']

    def initialize_from_player_state(self, player_state):
        self.hp             = player_state.hp
        self.action         = player_state.action
        self.bullets        = player_state.bullets
        self.grenades       = player_state.grenades
        self.shield_time    = player_state.shield_time
        self.shield_health  = player_state.shield_health
        self.num_shield     = player_state.num_shield
        self.num_deaths     = player_state.num_deaths

    @abstractmethod
    def update(self, pos_self, pos_opponent, action_self,
               action_opponent, action_opponent_is_valid):
        ...

    @abstractmethod
    def action_is_valid(self, action_self):
        ...


class PlayerStateStudent(PlayerStateBase):

    def action_is_valid(self, action_self):
            
        if action_self=='shoot':
            if self.bullets==0:
                return False
        elif action_self=='shield':
            if self.num_shield==0 or (time.time()-self.shield_start_time)<self.shield_max_time:
                return False
        elif action_self=='grenade':
            if self.grenades==0:
                return False
        elif action_self=='reload':
            if self.bullets>0:
                return False
        return True

    def update(self, pos_self, pos_opponent, action_self,
               action_opponent, action_opponent_is_valid):

        self.action         = action_self

        self.shield_time=round(max(self.shield_time-(time.time()-self.shield_start_time),0))
        if self.shield_time==0:
            self.shield_health=0
            
        if self.action_is_valid(action_self):
            if action_self=='shoot':
                self.bullets-=1
            elif action_self=='shield':
                self.num_shield-=1
                self.shield_time=self.shield_max_time
                self.shield_health=30 #defined in the GamePlay.pdf given
                self.shield_start_time=time.time()
            elif action_self=='grenade':
                self.grenades-=1
            elif action_self=='reload':
                self.bullets=self.magazine_size
        
        if (pos_self>=1 and pos_self<=3 and pos_opponent>=1 and pos_opponent<=3) or (pos_self==4 and pos_opponent==4) or (pos_self==0 and pos_opponent>=1 and pos_opponent<=3): #oppent can act on self
            if action_opponent_is_valid:
                if action_opponent=='shield':
                    pass
                elif action_opponent=='reload':
                    pass
                elif action_opponent=='none':
                    pass
                elif self.shield_time!=0: #there is an activated shield
                    if action_opponent=='shoot':
                        left_dmg=self.shield_health-self.bullet_hp
                        if left_dmg<0:
                            self.shield_health=0
                            self.hp=max(self.hp+left_dmg,0)
                        else:
                            self.shield_health=self.shield_health-self.bullet_hp
                    elif action_opponent=='grenade':
                        left_dmg=self.shield_health-self.grenade_hp
                        if left_dmg<0:
                            self.shield_health=0
                            self.hp=max(self.hp+left_dmg,0)
                        else:
                            self.shield_health=self.shield_health-self.grenade_hp
                elif action_opponent=='shoot':
                    self.hp=max(self.hp-self.bullet_hp,0)
                elif action_opponent=='grenade':
                    self.hp=max(self.hp-self.grenade_hp,0)
                
                
                            
        if self.hp==0:
            self.hp             = self.max_hp
            self.bullets        = self.magazine_size
            self.grenades       = self.max_grenades
            self.shield_time    = 0
            self.shield_health  = 0
            self.num_shield     = self.max_shields
            self.num_deaths     +=1        

