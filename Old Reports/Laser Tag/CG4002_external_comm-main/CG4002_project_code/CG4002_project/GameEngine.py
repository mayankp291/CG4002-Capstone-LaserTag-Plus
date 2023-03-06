import sys
import random

import Helper
from GameState import GameState

DEBUG_FLAG = False


class GameEngine:
    def _init_set_piece(self):
        # players can be 5 location 0-5
        # 0 is for moving out of range
        # 1-4 are the quadrants
        # 4 is protected under physical barrier

        # on disconnect
        self.set_piece_disconnect_1 = {'act_1': [Helper.Actions.shoot, Helper.Actions.shoot],
                                       'act_2': [Helper.Actions.shoot, Helper.Actions.shoot],
                                       'pos_1': [0, 1],
                                       'pos_2': [2, 3]}
        y = self._check_len(self.set_piece_disconnect_1, y=0)

        # on disconnect 2 players
        self.set_piece_disconnect_2 = {'act_1': [Helper.Actions.shoot, Helper.Actions.shoot],
                                       'act_2': [Helper.Actions.shoot, Helper.Actions.shoot],
                                       'pos_1': [0, 1],
                                       'pos_2': [0, 3]}
        y = self._check_len(self.set_piece_disconnect_1, y)

        x = [Helper.Actions.grenade]
        x.extend([Helper.Actions.shoot] * 4)
        x.append(Helper.Actions.grenade)
        self.set_piece_1 = {'act_1': x,
                            'act_2': [Helper.Actions.shield, Helper.Actions.grenade, Helper.Actions.shoot,
                                      Helper.Actions.grenade, Helper.Actions.shoot, Helper.Actions.reload],
                            'pos_1': [],
                            'pos_2': []}
        y = self._check_len(self.set_piece_1, y)

        x = [Helper.Actions.shield]
        x.extend([Helper.Actions.shoot] * 4)
        x.append(Helper.Actions.grenade)
        x_1 = [Helper.Actions.shoot] * 3
        x_1.extend([Helper.Actions.grenade, Helper.Actions.shoot, Helper.Actions.reload])
        self.set_piece_2 = {'act_1': x,
                            'act_2': x_1,
                            'pos_1': [],
                            'pos_2': []}
        y = self._check_len(self.set_piece_2, y)

    @staticmethod
    def _check_len(x, y):
        y += 1
        if len(x['act_1']) != len(x['act_2']):
            print("set_piece size mismatch", y)
            print(x['act_1'])
            print(x['act_2'])
            sys.exit()
        return y

    # test grenade
    # test shield
    # test physical barrier

    def __init__(self, is_single_player):
        self._init_set_piece()
        # initialize the game state
        self.game_state = GameState()

        # flag to show that player 2 position is irrelevant
        self.is_single_player = is_single_player

        # Generate the list of actions and positions
        # FIXME This is not needed
        self.actions_player_1   = [Helper.Actions.shoot]
        self.positions_player_1 = [1]
        self.actions_player_2   = [Helper.Actions.shoot]
        self.positions_player_2 = [3]
        self.print_data()

        n = len(self.set_piece_1['act_1'])
        self.actions_player_1.extend(self.set_piece_1['act_1'])
        self.actions_player_2.extend(self.set_piece_1['act_2'])
        self.__get_positions(n, self.positions_player_1)
        self.__get_positions(n, self.positions_player_2)
        self.print_data()

        self.actions_player_1.extend(self.set_piece_disconnect_1['act_1'])
        self.actions_player_2.extend(self.set_piece_disconnect_1['act_2'])
        self.positions_player_1.extend(self.set_piece_disconnect_1['pos_1'])
        self.positions_player_2.extend(self.set_piece_disconnect_1['pos_2'])
        self.print_data()

        n = len(self.set_piece_2['act_1'])
        self.actions_player_1.extend(self.set_piece_2['act_1'])
        self.actions_player_2.extend(self.set_piece_2['act_2'])
        self.__get_positions(n, self.positions_player_1)
        self.__get_positions(n, self.positions_player_2)
        self.print_data()

        if self.is_single_player:
            # las 2 actions will always be reload followed by shoot
            # but the student has to move out of the room to simulate a disconnect
            x = [Helper.Actions.reload, Helper.Actions.shoot]
            self.actions_player_1.extend(x)
            self.actions_player_2.extend(x)

        self.actions_player_1.append(Helper.Actions.logout)
        self.actions_player_2.append(Helper.Actions.logout)
        self.__get_positions(1, self.positions_player_1)
        self.__get_positions(1, self.positions_player_2)

        if self.is_single_player:
            # set all positions to 1
            n = len(self.actions_player_1)
            self.positions_player_1 = [1]*n
            self.positions_player_2 = [1]*n

            self.actions_player_2 = [Helper.Actions.no]*n

        self.print_data()

        self.cur_turn = 0

    @staticmethod
    def __get_positions(m, ret):
        prev_pos = ret[-1]
        for _ in range(m):
            r = random.random()
            if r < 0.4:
                next_pos = prev_pos + 1
            elif r < 0.8:
                next_pos = prev_pos + 3
            else:
                next_pos = prev_pos
            next_pos = (next_pos % 4) + 1  # modulo arithmetic with translation
            prev_pos = next_pos
            ret.append(prev_pos)

    def print_data(self):
        if DEBUG_FLAG:
            print (self.actions_player_1)
            print (self.actions_player_2)
            print (self.positions_player_1)
            print (self.positions_player_2)

    """
    Function moves one step in the game play and updates
    the health point and other details accordingly
    """
    def move_one_step(self):
        pos_p1 = self.positions_player_1[self.cur_turn]
        pos_p2 = self.positions_player_2[self.cur_turn]

        action_p1 = self.actions_player_1[self.cur_turn]
        action_p2 = self.actions_player_2[self.cur_turn]

        player_1 = self.game_state.player_1
        player_2 = self.game_state.player_2
        # check if actions are valid actions
        action_p1_is_valid = player_1.action_is_valid(action_p1)
        action_p2_is_valid = player_2.action_is_valid(action_p2)

        # change the state of player 1
        player_1.update (pos_p1, pos_p2, action_p1, action_p2, action_p2_is_valid)

        # change the state of player 2
        player_2.update (pos_p2, pos_p1, action_p2, action_p1, action_p1_is_valid)

        self.cur_turn += 1
