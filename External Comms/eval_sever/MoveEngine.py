import random

import Helper
from GameState import GameState

DEBUG_FLAG = False


class MoveEngine:
    def __init__(self, is_single_player, disable_gui):
        # initialize the game state
        self.game_state = GameState()

        # flag to show that player 2 position is irrelevant
        self.is_single_player = is_single_player

        # flag to show that this is a student release and the actions are fixed
        self.disable_gui = disable_gui

        def _init_list(_r):
            if _r > 0:
                ret = [Helper.Actions.shoot]
            else:
                ret = []
            ret.extend([Helper.Actions.shoot] * 6)
            ret.extend([Helper.Actions.shield] * 4)
            ret.extend([Helper.Actions.grenade] * 4)
            ret.extend([Helper.Actions.reload] * 4)
            random.shuffle(ret)
            return ret

        _a = _r = random.randint(0, 1)
        self.actions_player_1 = _init_list(_a)
        self.actions_player_2 = _init_list(_a)
        self.positions_player_1 = [1]
        self.positions_player_2 = [3]

        if not self.is_single_player:
            n = (len(self.actions_player_1) - 1) // 2
            self.__get_positions(n, self.positions_player_1)
            self.__get_positions(n, self.positions_player_2)
            # ask player one to move out
            self.positions_player_1.append(0)
            self.positions_player_2.append(3)

            n = len(self.actions_player_1) - len(self.positions_player_1) - 2
            self.__get_positions(n, self.positions_player_1)
            self.__get_positions(n, self.positions_player_2)
            # ask both players to move out
            self.positions_player_1.append(0)
            self.positions_player_2.append(0)

            n = len(self.actions_player_1) - len(self.positions_player_1)
            self.__get_positions(n, self.positions_player_1)
            self.__get_positions(n, self.positions_player_2)

        if self.disable_gui:
            self.actions_player_1 = [Helper.Actions.shield, Helper.Actions.grenade, Helper.Actions.reload,
                                     Helper.Actions.shoot, Helper.Actions.shoot, Helper.Actions.shield,
                                     Helper.Actions.shoot, Helper.Actions.shoot, Helper.Actions.reload,
                                     Helper.Actions.shield, Helper.Actions.grenade, Helper.Actions.shield,
                                     Helper.Actions.shoot, Helper.Actions.shield, Helper.Actions.shoot,
                                     Helper.Actions.shoot, Helper.Actions.reload, Helper.Actions.shoot,
                                     Helper.Actions.shoot, Helper.Actions.grenade, Helper.Actions.grenade,
                                     Helper.Actions.grenade, Helper.Actions.grenade, Helper.Actions.reload,
                                     Helper.Actions.shoot, Helper.Actions.shoot, Helper.Actions.reload,
                                     Helper.Actions.reload, Helper.Actions.shield, Helper.Actions.reload,
                                     Helper.Actions.shield, Helper.Actions.shoot, Helper.Actions.grenade]
            self.actions_player_2 = [Helper.Actions.reload, Helper.Actions.shield, Helper.Actions.shoot,
                                     Helper.Actions.grenade, Helper.Actions.grenade, Helper.Actions.shoot,
                                     Helper.Actions.shield, Helper.Actions.grenade, Helper.Actions.reload,
                                     Helper.Actions.reload, Helper.Actions.shoot, Helper.Actions.shoot,
                                     Helper.Actions.shoot, Helper.Actions.grenade, Helper.Actions.grenade,
                                     Helper.Actions.shoot, Helper.Actions.shield, Helper.Actions.shoot,
                                     Helper.Actions.shield, Helper.Actions.reload, Helper.Actions.shoot,
                                     Helper.Actions.shoot, Helper.Actions.shield, Helper.Actions.shoot,
                                     Helper.Actions.shield, Helper.Actions.reload, Helper.Actions.reload,
                                     Helper.Actions.shoot, Helper.Actions.reload, Helper.Actions.grenade,
                                     Helper.Actions.grenade, Helper.Actions.shield, Helper.Actions.shoot]
            # set all positions to 1
            n = len(self.actions_player_1)
            self.positions_player_1 = [1]*n
            self.positions_player_2 = [1]*n

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
            prev_pos -= 1
            r = random.random()
            if r < 0.49:
                next_pos = prev_pos + 1
            elif r < 0.98:
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
