from config import *
import search
import random
import time
import datetime
random.seed(time.time())


class player:
    def __init__(self, is_b, player_type):
        assert player_type in ["human", "ai"]
        self.type = player_type
        self.is_b = is_b
        self.elaspled_time = 0.

    def get_strategy(self, board):
        pass

    def get_elapsed_time(self):
        return str(datetime.timedelta(seconds=int(self.elaspled_time)))

class human_player(player):
    def __init__(self, is_b, player_type):
        super().__init__(is_b, player_type)
        self.name = "human"
        self.start_time = 0.

    def get_strategy(self, board):
        pass

    def timer_tic(self):
        self.start_time = time.time()

    def time_update(self):
        self.elaspled_time += time.time() - self.start_time

class ai_player(player):
    def __init__(self, is_b, player_type, ai_level):
        super().__init__(is_b, player_type)
        self.name = "ai   "
        max_depth, search_range, max_pos_move, max_pos_move_first = self._ai_level_to_para(ai_level)
        self.engine = search.absearch(max_depth, search_range, max_pos_move, max_pos_move_first)
        self._init_strategy() # move_strategy

    def get_strategy(self, board):
        time_start = time.time()
        time.sleep(0.1)
        dest = self.begin_strategy(board)
        if dest == None:
            dest = self.engine.get_strategy(board)
        self.elaspled_time += time.time() - time_start
        return dest

    def _ai_level_to_para(self, ai_level):
        if ai_level == 0:
            max_depth=1
            search_range=[2, 1]
            max_pos_move=6
            max_pos_move_first=20

        if ai_level == 1:
            max_depth=2
            search_range=[2, 1]
            max_pos_move=6
            max_pos_move_first=20

        if ai_level == 2:
            max_depth=4
            search_range=[2, 1]
            max_pos_move=6
            max_pos_move_first=20

        if ai_level == 3:
            max_depth=5
            search_range=[2, 1]
            max_pos_move=6
            max_pos_move_first=20

        return max_depth, search_range, max_pos_move, max_pos_move_first

    def begin_strategy(self, board):
        dest = None
        mid = BOARD_SIZE // 2
        if 0 == board.current_round:
            dest = (mid, mid)
        if 1 == board.current_round:
            if board.get_last_move(is_padded=False) == (mid, mid):
                dest = random.choice(self.move_strategy[1])
        return dest

    def _init_strategy(self):
        self.move_strategy = dict()
        mid = BOARD_SIZE // 2
        self.move_strategy[1] = [(mid, mid+1), (mid, mid-1), (mid+1, mid), (mid-1, mid), (mid-1, mid-1), (mid+1, mid+1), (mid+1, mid-1), (mid-1, mid+1)]