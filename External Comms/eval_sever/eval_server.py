import json
import pandas as pd
import os
import sys
import random as random
import time
import tkinter as tk
from _socket import SHUT_RDWR
import socket
import threading
import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import traceback
from queue import Queue

from tkinter import ttk
from tkinter.constants import HORIZONTAL, VERTICAL

from MoveEngine import MoveEngine
from GameState import GameState
from Helper import ice_print_debug
from PlayerState import PlayerStateBase


# Global flags
DISABLE_GUI             = False     # the server will not display any GUI
SINGLE_PLAYER_MODE      = False     # the server is for 1-player test
DEBUG_FLAG              = False
CLOSE_WINDOW            = False     # close the GUI

LOG_DIR = os.path.join(os.path.dirname(__file__), 'evaluation_logs')
message_queue = Queue()     # message to be displayed on the window


class TurnGenerator:
    """
    Class that will generate randomized list of actions.
    Actions will be displayed on the evaluation server UI for the
    players to follow.
    """
    def __init__(self):
        self.cur_turn = -1
        self.game_engine = MoveEngine(is_single_player=SINGLE_PLAYER_MODE,
                                      disable_gui=DISABLE_GUI)

        # Generate random sequence of actions for Player 1
        self.p1_actions     = self.game_engine.actions_player_1
        self.p1_positions   = self.game_engine.positions_player_1
        if DEBUG_FLAG:
            print("Actions:   ", self.p1_actions)
            print("Positions: ", self.p1_positions)

        # Generate random sequence of actions for Player 2
        self.p2_actions     = self.game_engine.actions_player_2
        self.p2_positions   = self.game_engine.positions_player_2
        if DEBUG_FLAG:
            print("Actions:   ", self.p2_actions)
            print("Positions: ", self.p2_positions)

    """
    Called at the start of every turn to generate new values for player actions
    """
    def iterate(self):
        # Return True if we have finished going through all turns
        if self.cur_turn + 1 >= len(self.p1_actions):
            return True

        # we need to generate the action
        self.cur_turn += 1
        self.game_engine.move_one_step()

        # display the location where players are to stand
        if not SINGLE_PLAYER_MODE:
            print(f"New P1 Position: {self.get_display_position()[0]}")
            print(f"New P2 Position: {self.get_display_position()[1]}")
            message_queue.put(self.get_display_position()[0])
            message_queue.put(self.get_display_position()[1])

            # we want to ensure students are in the correct position
            _ = input("Press enter when players are in correct position : ")
        else:
            # we are in single player mode
            # to test the bluetooth disconnection we will ask the student to step out
            if self.cur_turn == (len(self.p1_actions) - 2):
                print(f"New P1 Position: 0")
                message_queue.put('0')
                # we want to ensure students are in the correct position
                _ = input("Press enter when player is in correct position : ")

        print(f"New P1 Action: {self.p1_actions[self.cur_turn]}")
        message_queue.put(self.p1_actions[self.cur_turn])
        if not SINGLE_PLAYER_MODE:
            print(f"New P2 Action: {self.p2_actions[self.cur_turn]}")
            message_queue.put(self.p2_actions[self.cur_turn])

        return False

    def get_correct_action(self):
        """
        Return both player expected actions in tuple of tuples: (p1_action,p2_action)
        """
        return self.p1_actions[self.cur_turn], self.p2_actions[self.cur_turn]

    def get_display_position(self):
        """
        Return both player expected positions in tuple of tuples: (p1_position,p2_position)
        """
        return str(self.p1_positions[self.cur_turn]), str(self.p2_positions[self.cur_turn])


class Server(threading.Thread):
    """
    class to start the eval server
    """
    def __init__(self, port_num, group_id):
        super().__init__()

        # Create a TCP/IP socket and bind to portNone
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        server_address = ('', port_num)
        print('starting up on %s port %s' % server_address)
        server_socket.bind(server_address)

        # Setup logger
        if DISABLE_GUI:
            self.log_filename_csv  = 'group{}_cli_logs.csv'.format(group_id)
            self.log_filename_json = 'group{}_cli_logs.json'.format(group_id)
        else:
            self.log_filename_csv  = 'group{}_logs.csv'.format(group_id)
            self.log_filename_json = 'group{}_logs.json'.format(group_id)
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR)
        self.log_filepath_csv = os.path.join(LOG_DIR, self.log_filename_csv)
        self.log_filepath_json = os.path.join(LOG_DIR, self.log_filename_json)
        self.columns = [
            'timestamp', 'id', 'p1_action', 'gt_p1_action', 'p2_action', 'gt_p2_action',
            'response_time', 'is_p1_action_correct', 'is_p2_action_correct'
        ]
        self.df = pd.DataFrame(columns=self.columns)
        self.df = self.df.set_index('timestamp')

        # used to distinguish 2 different usages of eval_server for the same group
        # not foolproof, needs manual verification
        self.random_id = random.randint(1, 10*1000)

        # Setup turns
        self.turn_gen           = TurnGenerator()   # Initialize turn generator
        self.action_set_time    = 0         # Time turn instructions/actions were set by eval_server
        self.turn_wait_timeout  = 60        # Turn response timeout amount
        self.turn_wait_timer    = None      # Timer object to keep track of turn response timeout

        # Temporary storage for correct actions for each player
        self.last_p1_action = None
        self.last_p2_action = None

        # Ultra96 Connection things
        self.server_socket  = server_socket
        self.connection     = None  # Ultra96 connection object
        self.secret_key     = None  # AES secret key

        self.has_no_response    = True  # Flag set when there was no response from Ultra96
        self.expecting_packet   = threading.Event()  # indicates weather
        self.shutdown           = threading.Event()  # indicates that the thread has to die

    @staticmethod
    def game_state_diff(expected, received):
        game_state_expected = PlayerStateBase()
        game_state_received = PlayerStateBase()
        game_state_expected.initialize_from_dict(expected)
        game_state_received.initialize_from_dict(received)
        diff_dict = game_state_expected.get_difference(game_state_received)
        return diff_dict

    def setup_connection(self):
        """
            This function waits for a connection from an Ultra96 and
            then reads the encryption key for the Ultra96's messages from STDIN.
            Returns the encryption key.
        """
        # FIXME
        ipaddress_dict = {
            '192.168.95.224': 'B01',
            '192.168.95.225': 'B02',
            '192.168.95.226': 'B03',
            '192.168.95.246': 'B04',
            '192.168.95.223': 'B05',
            '192.168.95.222': 'B06',
            '192.168.95.220': 'B07',
            '192.168.95.250': 'B08',
            '192.168.95.219': 'B10',
            '192.168.95.234': 'B11',
            '192.168.95.235': 'B12',
            '192.168.95.236': 'B13',
            '192.168.95.221': 'B14',
            '192.168.95.247': 'B15',
            '192.168.95.248': 'B16',
            '192.168.95.244': 'B17',
            '192.168.95.249': 'B18',
            '192.168.95.243': 'B19'}
        # Wait for a connection
        print('Waiting for a connection')
        self.connection, client_address = self.server_socket.accept()
        print('--------------------------------------------------')
        print('        Connected to:', client_address[0])
        # print('                     ', ipaddress_dict[client_address[0]])  
        print('--------------------------------------------------')

        if DISABLE_GUI:
            secret_key = "PLSPLSPLSPLSWORK"
        else:
            secret_key = "PLSPLSPLSPLSWORK"
            # print("Enter the secret key: ")
            # secret_key = sys.stdin.readline().strip()

        print('connection from', client_address)
        if len(secret_key) == 16 or len(secret_key) == 24 or len(secret_key) == 32:
            # set the correct values for game state based on first action and update the cur_turn
            self.iterate()
        else:
            print("AES key must be either 16, 24, or 32 bytes long")
            self.stop()

        return secret_key

    def setup_turn(self):
        """
        This function executes every turn to set the actions for the 2 players.
        It first cancels the turn wait timer since the previous turn has ended and checks if we
        received a response from the Ultra96 in the previous turn.
        Next, it uses the TurnGenerator object to generate new actions and restarts
        the turn wait timer.
        """
        if self.turn_wait_timer:
            self.turn_wait_timer.cancel()
            self.turn_wait_timer = None

        if self.has_no_response:  # If no response was sent by Ultra96
            self.write_turn_to_logger("None", "None", "None", "None", {}, {})
            print("TURN TIMEOUT")
            # Send turn state update even at timeout
            if not self.send_update(self.turn_gen.game_engine.game_state):
                self.stop()
                return

        self.iterate()

    def iterate(self):
        # Generate new actions using the TurnGenerator object
        self.expecting_packet.clear()
        finished = self.turn_gen.iterate()
        # Check if no more turns left
        if finished:
            self.stop()
        else:
            # Get correct expected actions for checking once received Ultra96 response
            self.last_p1_action, self.last_p2_action = self.turn_gen.get_correct_action()

            # Used to calculate time taken to get response from Ultra96
            self.action_set_time = time.time()

            # Restart turn wait timer
            self.turn_wait_timer = threading.Timer(self.turn_wait_timeout, self.setup_turn)
            self.has_no_response = True
            self.turn_wait_timer.start()
            self.expecting_packet.set()

    def write_turn_to_logger(self,
                             predicted_p1_action: str, correct_p1_action: str,
                             predicted_p2_action: str, correct_p2_action: str,
                             game_state_received: dict, game_state_expected: dict):
        """
        Write data to logger.
        """
        _flag_write_csv     = True
        _flag_write_json    = True
        if _flag_write_csv:
            log_filepath = self.log_filepath_csv
            if not os.path.exists(log_filepath):  # first write
                with open(log_filepath, 'w') as f:
                    self.df.to_csv(f)

            with open(log_filepath, 'a') as f:
                data = dict()
                data['timestamp']   = time.time()
                data['id']          = self.random_id

                data['p1_action']       = predicted_p1_action
                data['gt_p1_action']    = correct_p1_action
                data['p2_action']       = predicted_p2_action
                data['gt_p2_action']       = correct_p2_action

                data['response_time']        = data['timestamp'] - self.action_set_time
                data['is_p1_action_correct'] = (predicted_p1_action == correct_p1_action)
                data['is_p2_action_correct'] = (predicted_p2_action == correct_p2_action)

                self.df = pd.DataFrame(data, index=[0])[self.columns].set_index('timestamp')
                self.df.to_csv(f, header=False)

        if _flag_write_json:
            data = dict()
            data['id']                  = self.random_id
            data['timestamp']           = time.time()
            data['response_time']       = data['timestamp'] - self.action_set_time
            data['game_state_received'] = game_state_received
            data['game_state_expected'] = game_state_expected

            log_filepath = self.log_filepath_json
            mode = 'a'
            if not os.path.exists(log_filepath):  # first write
                mode = 'w'

            with open(log_filepath, mode) as f:
                f.write(json.dumps(data)+'\n')

    def send_update(self, game_state: GameState):
        """
        Send last expected action to Ultra96.
        """
        success = game_state.send_plaintext(self.connection)
        return success

    def stop(self):
        """
        Closes server upon end of assessment, after Ultra96 disconnects/sends logout message.
        """
        try:
            self.connection.shutdown(SHUT_RDWR)
            self.connection.close()
        except OSError:
            # connection already closed
            pass

        if self.turn_wait_timer:
            self.turn_wait_timer.cancel()
            self.turn_wait_timer = None
        self.shutdown.set()
        message_queue.put("BYE")

        print("bye ", end='')

    def decrypt_message(self, cipher_text):
        """
        This function decrypts the response message received from the Ultra96 using the secret encryption key
        that was entered in this script during initial connection by the Ultra96.
        It returns a dictionary containing the action detected by the Ultra96.
        """
        decoded_message = base64.b64decode(cipher_text)                            # Decode message from base64 to bytes
        iv              = decoded_message[:AES.block_size]                                     # Get IV value
        secret_key      = bytes(str(self.secret_key), encoding="utf8")             # Convert secret key to bytes

        cipher = AES.new(secret_key, AES.MODE_CBC, iv)                              # Create new AES cipher object

        decrypted_message = cipher.decrypt(decoded_message[AES.block_size:])  # Perform decryption
        decrypted_message = unpad(decrypted_message, AES.block_size)
        decrypted_message = decrypted_message.decode('utf8')  # Decode bytes into utf-8

        ret = json.loads(decrypted_message)
        return ret

    def recv_game_state(self):
        game_state_received = None
        try:
            # recv length followed by '_' followed by cypher
            data = b''
            while not data.endswith(b'_'):
                _d = self.connection.recv(1)
                if not _d:
                    data = b''
                    break
                data += _d
            if len(data) == 0:
                print('no more data from the client')
                self.stop()

            data = data.decode("utf-8")
            length = int(data[:-1])

            data = b''
            while len(data) < length:
                _d = self.connection.recv(length - len(data))
                if not _d:
                    data = b''
                    break
                data += _d
            if len(data) == 0:
                print('no more data from the client')
                self.stop()
            msg = data.decode("utf8")  # Decode raw bytes to UTF-8
            game_state_received = self.decrypt_message(msg)
        except ConnectionResetError:
            print('Connection Reset')
            self.stop()
        return game_state_received

    def run(self):
        """
        Main loop of server. This function performs a blocking wait for data from the Ultra96 until the Ultra96
        disconnected. The data it receives is decrypted and is written to the logger. Lastly, the function sends
        the correct turn data (action) to the Ultra96 and sets up the next turn.
        """
        self.expecting_packet.clear()
        # Listen for incoming connections
        self.server_socket.listen(1)
        self.secret_key = self.setup_connection()      # Wait for secret key from Ultra96

        while not self.shutdown.is_set():
            try:
                game_state_received = self.recv_game_state()
                if game_state_received is None:
                    # we are about to terminate
                    continue
                if self.expecting_packet.is_set():
                    self.expecting_packet.clear()
                else:
                    # there was some timing issue, we need to discard this packet
                    ice_print_debug("Discarding: unexpected packet received")
                    # we would send a response nevertheless
                    _game_state_correct = self.turn_gen.game_engine.game_state
                    if not self.send_update(_game_state_correct):
                        self.stop()
                    continue

                self.has_no_response = False

                # Store last action data for sending back to Ultra96 since self.setup_turn() overwrites data
                correct_p1_action = self.last_p1_action
                correct_p2_action = self.last_p2_action

                _game_state_correct = self.turn_gen.game_engine.game_state

                self.write_turn_to_logger(
                    game_state_received['p1']['action'],
                    correct_p1_action,
                    game_state_received['p2']['action'],
                    correct_p2_action,
                    game_state_received, _game_state_correct.get_dict()
                )

                ice_print_debug("")
                ice_print_debug("------   ", self.turn_gen.cur_turn, "   ------")
                ice_print_debug("Received P1: ", game_state_received['p1'], color=1)
                ice_print_debug("Expected P1: ", _game_state_correct.player_1.get_dict(), color=1)
                ice_print_debug("Received P2: ", game_state_received['p2'], color=3)
                ice_print_debug("Expected P2: ", _game_state_correct.player_2.get_dict(), color=3)
                if True:
                    diff_p1 = self.game_state_diff(_game_state_correct.player_1.get_dict(), game_state_received['p1'])
                    diff_p2 = self.game_state_diff(_game_state_correct.player_2.get_dict(), game_state_received['p2'])
                    ice_print_debug("diff P1: ", diff_p1, color=1)
                    ice_print_debug("diff P2: ", diff_p2, color=3)

                # Send last action and new grid data to Ultra96
                if not self.send_update(_game_state_correct):
                    self.stop()
                else:
                    self.setup_turn()        # Setup new turn to get new grid data

            except Exception as _:
                traceback.print_exc()
                self.stop()

        print("bye:")
        global CLOSE_WINDOW
        CLOSE_WINDOW = True


class Eval:
    """
    The main evaluation class
    """
    def __init__(self, port_num, group_id):
        self.p1_action_text     = None
        self.p2_action_text     = None
        self.max_num_actions    = 0
        self.p2_frame   = None
        self.p1_frame   = None
        self.turn_text  = None
        self.port_num   = port_num
        self.group_id   = group_id

        # start the server
        self.server = Server(self.port_num, self.group_id)
        self.server.start()

        # Initialize base window
        self.display_window = tk.Tk()

    def check_loop_status(self):
        """
        Function to periodically update GUI
        """
        global CLOSE_WINDOW
        while True:     # enables us to have a single point of return from the function
            if CLOSE_WINDOW:
                self.display_window.destroy()  # OK in this function.
            else:
                text = message_queue.get()
                if text == 'BYE':
                    break
                self.p1_action_text.set(text)

                if not SINGLE_PLAYER_MODE:
                    text = message_queue.get()
                    if text == 'BYE':
                        break
                    self.p2_action_text.set(text)

                self.turn_text.set(f"{self.server.turn_gen.cur_turn + 1} / {self.max_num_actions + 1}")
                self.display_window.update()
            break

        self.display_window.after(10, self.check_loop_status)  # Check again after delay.

    def start(self):
        """
        The main function
        """
        global DISABLE_GUI
        global SINGLE_PLAYER_MODE

        if not DISABLE_GUI:
            # Draw the window
            self.display_window.title = "Evaluation Server"
            main_frame = tk.Frame(
                self.display_window
            )
            main_frame.pack(expand=True, fill='both')

            # Finished turns
            self.turn_text = tk.StringVar()
            turn_label = tk.Label(main_frame, textvariable=self.turn_text, font=("times", 80))
            turn_label.pack(fill='x')

            # Player 1 column
            self.p1_frame = tk.Frame(main_frame, bg="red")
            self.p1_frame.pack(expand=True, fill='both', side='left')
            # Player 1 title
            p1_label = tk.Label(self.p1_frame, text="Player 1", font=('times', 100, 'bold'), bg="red")
            p1_label.pack(ipady=20)
            # Player 1 variable frame
            p1_var_frame = tk.Frame(self.p1_frame, bg='#ffcccb')
            p1_var_frame.pack(expand=True, fill='both')
            # Player 1 action variable
            self.p1_action_text = tk.StringVar()
            p1_action_label = tk.Label(p1_var_frame, textvariable=self.p1_action_text,
                                       font=("times", 100), bg='#ffcccb')
            p1_action_label.pack(expand=True)
            # Player 2 variable separator
            p1_var_sep = ttk.Separator(p1_var_frame, orient=HORIZONTAL)
            p1_var_sep.pack(expand=True, fill='x')

            if not SINGLE_PLAYER_MODE:
                # Player 2 column
                self.p2_frame = tk.Frame(main_frame, bg="blue")
                self.p2_frame.pack(expand=True, fill='both', side='right')
                # Player 2 title
                p2_label = tk.Label(self.p2_frame, text="Player 2", font=('times', 100, 'bold'), bg="blue")
                p2_label.pack(ipady=20)
                # Player 2 variable frame
                p2_var_frame = tk.Frame(self.p2_frame, bg='#add8e6')
                p2_var_frame.pack(expand=True, fill='both')
                # Player 2 action variable
                self.p2_action_text = tk.StringVar()
                p2_action_label = tk.Label(p2_var_frame, textvariable=self.p2_action_text,
                                           font=("times", 100), bg='#add8e6')
                p2_action_label.pack(expand=True)
                # Player 2 variable separator
                p2_var_sep = ttk.Separator(p2_var_frame, orient=HORIZONTAL)
                p2_var_sep.pack(expand=True, fill='x')

                # Player column separator
                col_sep = ttk.Separator(main_frame, orient=VERTICAL)
                col_sep.pack(expand=True, fill='y')

            # Update window based on data in server
            self.display_window.update()
            self.max_num_actions = len(self.server.turn_gen.p1_actions) - 1
            # display none till connection established
            self.turn_text.set(f"0 / {self.max_num_actions + 1}  G{self.group_id}")
            self.p1_action_text.set('none')
            if not SINGLE_PLAYER_MODE:
                self.p2_action_text.set('none')
            self.display_window.update()

            self.check_loop_status()  # Start periodic checking.
            self.display_window.mainloop()
            print ('closing window')
            self.server.join()
        else:
            # wait for the server to terminate
            try:
                self.server.join()
            except KeyboardInterrupt:
                self.server.stop()


if __name__ == '__main__':
    _num_para = 4
    if len(sys.argv) < _num_para:
        print('Invalid number of arguments')
        print('python3 ' + os.path.basename(__file__) + ' [Port] [groupID] [mode]')
        print('port   : The port number for the TCP server')
        print('groupID: Identifier of the group being evaluated')
        print('mode   : Takes value 1 for single player and 2 for double player')
        sys.exit()
    elif len(sys.argv) > _num_para:
        DISABLE_GUI = True
        print("This is the eval server meant for terminal mode, this is for students to tryout their eval client")
    if int(sys.argv[_num_para - 1]) == 1:
        print("               SINGLE PLAYER MODE")
        SINGLE_PLAYER_MODE = True
    else:
        print("               DOUBLE PLAYER MODE")
        SINGLE_PLAYER_MODE = False

    # initialization
    _port_num = int(sys.argv[1])
    _group_id = sys.argv[2]

    evaluation = Eval(_port_num, _group_id)
    evaluation.start()
