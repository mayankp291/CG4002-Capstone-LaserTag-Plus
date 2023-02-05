import json
import random
from StateStaff import StateStaff
from PlayerState import PlayerStateBase


class GameState:
    """
    class for sending and receiving the game state json object
    """
    def __init__(self):
        self.player_1 = StateStaff()
        self.player_2 = StateStaff()

    def get_dict(self):
        data = {'p1': self.player_1.get_dict(), 'p2': self.player_2.get_dict()}
        return data

    def _get_data_plain_text (self):
        data = self.get_dict()
        return json.dumps(data)

    # send the game state json to remote host
    def send_plaintext(self, remote_socket):
        success = True
        plaintext = self._get_data_plain_text()

        # ice_print_debug(f"Sending message to client: {plaintext} (Unencrypted)")
        # send len followed by '_' followed by cypher
        m = str(len(plaintext))+'_'
        try:
            remote_socket.sendall(m.encode("utf-8"))
            remote_socket.sendall(plaintext.encode("utf-8"))
        except OSError:
            print("Connection terminated")
            success = False
        return success

    def init_player (self, player_id, action, hp, bullets_remaining, grenades_remaining,
                     shield_time_remaining, shield_health, num_unused_shield, num_deaths):
        if player_id == 1:
            player = self.player_1
        else:
            player = self.player_2
        player.initialize(action, bullets_remaining, grenades_remaining, hp,
                          num_deaths, num_unused_shield,
                          shield_health, shield_time_remaining)

    def init_players_random (self):
        for player_id in [1, 2]:
            action = random.choice(['shoot', 'shield', 'grenade', 'reload', 'none'])
            hp = random.randint(10, 90)
            bullets_remaining = random.randint(0, 6)
            grenades_remaining = random.randint(0, 3)
            shield_time_remaining = random.randint(0, 30)
            shield_health = random.randint(0, 30)
            num_unused_shield = random.randint(0, 3)
            num_deaths = random.randint(0, 3)

            self.init_player(player_id, action, bullets_remaining, grenades_remaining, hp,
                             num_deaths, num_unused_shield,
                             shield_health, shield_time_remaining)

    def init_players (self, player_1: PlayerStateBase, player_2: PlayerStateBase):
        self.player_1.initialize_from_player_state(player_1)
        self.player_2.initialize_from_player_state(player_2)
