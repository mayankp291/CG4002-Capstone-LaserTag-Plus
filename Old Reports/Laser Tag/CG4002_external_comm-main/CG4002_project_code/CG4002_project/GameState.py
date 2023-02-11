import json
import random
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import base64
from PlayerState import PlayerStateStudent
from PlayerState import PlayerStateBase
from Helper import ice_print_debug


class GameState:
    """
    class for sending and receiving the game state json object
    """
    def __init__(self):
        self.player_1 = PlayerStateStudent()
        self.player_2 = PlayerStateStudent()

    def _get_data_plain_text (self):
        data = {'p1': self.player_1.get_dict(), 'p2': self.player_2.get_dict()}
        return json.dumps(data)+'#'
    
    def _get_data_plain_text_phone(self):
        data = {'p1': self.player_1.get_dict(), 'p2': self.player_2.get_dict()}
        return json.dumps(data)
    
    # encrypt and send the game state json to remote host
    def send_encrypted(self, remote_socket, secret_key_string):
        success = True
        plaintext = self._get_data_plain_text()

        ice_print_debug(f"Sending message to server: {plaintext} (Unencrypted)")
        plaintext_bytes = pad(plaintext.encode("utf-8"), 16)

        secret_key_bytes = secret_key_string.encode("utf-8")
        cipher = AES.new(secret_key_bytes, AES.MODE_CBC)
        iv_bytes = cipher.iv

        ciphertext_bytes = cipher.encrypt(plaintext_bytes)
        message = base64.b64encode(iv_bytes + ciphertext_bytes)

        # send len followed by '_' followed by cypher

        m = str(len(message))+'_'
        try:
            remote_socket.sendall(m.encode("utf-8"))
            remote_socket.sendall(message)
        except OSError:
            print("Connection terminated")
            success = False
        return success

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

    # recv the game state json from remote host and update the object
    def recv_and_update(self, remote_socket):
        success = False
        while True:
            # recv length followed by '_' followed by cypher
            data = b''
            while not data.endswith(b'_'):
                _d = remote_socket.recv(1)
                if not _d:
                    data = b''
                    break
                data += _d
            if len(data) == 0:
                print('no more data from', remote_socket)
                break

            data = data.decode("utf-8")
            length = int(data[:-1])

            data = b''
            while len(data) < length:
                _d = remote_socket.recv(length - len(data))
                if not _d:
                    data = b''
                    break
                data += _d
            if len(data) == 0:
                print('no more data from', remote_socket)
                break
            msg = data.decode("utf8")  # Decode raw bytes to UTF-8
            msg = msg.split('#')[0]
            game_state_received = json.loads(msg)

            ice_print_debug(game_state_received)
            self.player_1.initialize_from_dict(game_state_received['p1'])
            self.player_2.initialize_from_dict(game_state_received['p2'])
            success = True
            break
        #print(f"in recv_update:\n {self._get_data_plain_text_phone()}")
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
