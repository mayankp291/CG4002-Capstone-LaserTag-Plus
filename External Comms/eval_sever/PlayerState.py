import time
from abc import abstractmethod


class PlayerStateBase:
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

    def get_difference(self, game_state_received):
        diff_dict = dict()

        if self.action is None:
            diff_dict['action_expected'] = 'none'
        else:
            diff_dict['action_expected'] = self.action.lower()
        if game_state_received.action is None:
            diff_dict['action_received'] = 'none'
        else:
            diff_dict['action_received'] = game_state_received.action.lower()
        if diff_dict['action_expected'] == diff_dict['action_received']:
            diff_dict['action_matched'] = 'True'
        else:
            diff_dict['action_matched'] = 'False'
        self._get_difference_helper(diff_dict, self.hp, game_state_received.hp, 'hp')
        self._get_difference_helper(diff_dict, self.bullets, game_state_received.bullets, 'bullets')
        self._get_difference_helper(diff_dict, self.grenades, game_state_received.grenades, 'grenades')
        self._get_difference_helper(diff_dict, self.shield_time, game_state_received.shield_time, 'shield_time')
        self._get_difference_helper(diff_dict, self.shield_health, game_state_received.shield_health, 'shield_health')
        self._get_difference_helper(diff_dict, self.num_shield, game_state_received.num_shield, 'num_shield')
        self._get_difference_helper(diff_dict, self.num_deaths, game_state_received.num_deaths, 'num_deaths')

        return diff_dict

    @staticmethod
    def _get_difference_helper(diff_dict, e, r, val):
        if e != r:
            diff_dict[val] = e - r

    def initialize_from_dict(self, player_dict: dict):
        self.hp             = int(player_dict['hp'])
        self.action         = player_dict['action']
        self.bullets        = int(player_dict['bullets'])
        self.grenades       = int(player_dict['grenades'])
        self.shield_time    = float(player_dict['shield_time'])
        self.shield_health  = int(player_dict['shield_health'])
        self.num_shield     = int(player_dict['num_shield'])
        self.num_deaths     = int(player_dict['num_deaths'])

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
