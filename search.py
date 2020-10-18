from config import *
import numpy as np
import pickle
import itertools
import random
import time

random.seed(time.time())

time_ = 0

class absearch:
    def __init__(self, max_depth=4, search_range=[2, 1], max_pos_move=6, max_pos_move_first=10):
        self.max_depth = max_depth
        self.max_pos_move_first = max_pos_move_first
        self.search_range = search_range
        self.max_pos_move = max_pos_move
        self.value_board = valueBoard()

        assert search_range[0] <= PAD_SIZE and search_range[1] <= PAD_SIZE

    def get_strategy(self, board):
        time_start = time.time()
        global time_
        time_ = 0

        is_win, list_must_move = self._short_cut_eval(board)
        possible_moves = self._find_all_moves(board)
        possible_moves, board_values = self._sort_possible_moves(board, possible_moves)
        dest = possible_moves[0]
        best_val = -INF
        self.value_cache = dict() # cache the result to speed up searching
        count_remain_seach = self.max_pos_move_first
        for each_move, board_value in zip(possible_moves, board_values):
            board.move(each_move, is_dest_padded=True)
            is_win_tmp, list_must_move_tmp = self._short_cut_eval(board)
            board.revert_move()
            if 2 == is_win_tmp:
                dest = each_move
                break
            elif each_move in list_must_move or (len(list_must_move)==0 and count_remain_seach>0) or (len(list_must_move)==0 and is_win_tmp > 0):
                board.move(each_move, is_dest_padded=True)
                each_val = self._search(board, best_val, self.max_depth+(each_move in list_must_move), is_win_tmp, list_must_move_tmp, board_value)
                board.revert_move()
                if len(list_must_move)==0 and is_win_tmp == 0:
                    count_remain_seach -= 1
                if each_val > best_val:
                    best_val = each_val
                    dest = each_move
            # print(board.current_round, each_move, each_val, best_val)

        print("Overall time {:.1f} s".format(time.time()-time_start))
        print("Hash time {:.1f} s".format(time_))

        return board.padded_dest_to_dest(dest)

    def _search(self, board, current_max, depth, is_win, list_must_move, board_value):
        if IS_DEBUG:
            global time_
        try:
            return self.value_cache[board.encode_board()]
        except:
            pass
        if 0 < is_win:
            res = INF - board.current_round + is_win
            self.value_cache[board.encode_board()] = res
            return res
        if depth == 0:
            self.value_cache[board.encode_board()] = board_value
            return board_value
        possible_moves = self._find_all_moves(board)
        depth = depth - 1 
        possible_moves, board_values = self._sort_possible_moves(board, possible_moves)
        best_val = -INF
        count_remain_search = self.max_pos_move
        for each_move, board_value in zip(possible_moves, board_values):
            board.move(each_move, is_dest_padded=True)
            is_win_tmp, list_must_move_tmp = self._short_cut_eval(board)
            board.revert_move()
            if 2 == is_win_tmp or each_move in list_must_move or (len(list_must_move) == 0 and count_remain_search > 0) or (len(list_must_move) == 0 and 0 < is_win_tmp):
                board.move(each_move, is_dest_padded=True)
                each_val = self._search(board, best_val, depth+(each_move in list_must_move), is_win_tmp, list_must_move_tmp, board_value)
                board.revert_move()
                if len(list_must_move) == 0 and is_win_tmp == 0:
                    count_remain_search -= 1
                if -each_val <= current_max:
                    self.value_cache[board.encode_board()] = -each_val
                    return -each_val
                elif each_val >best_val:
                    best_val = each_val
        self.value_cache[board.encode_board()] = -best_val
        return -best_val

    def _short_cut_eval(self, board):
        """Judge whether it is a winning situation and return the list_must_move"""
        list_type, list_must_move = board.move_status()
        is_win = board._is_win_advanced(list_type, list_must_move)
        return is_win, list_must_move

    def _find_all_moves(self, board):
        if 0 == board.current_round:
            mid = board.SIZE // 2
            return board.dest_to_padded_dest((mid, mid))
        if True == board.is_b:
            my_board = board.b
            my_not_board = board.not_b
            oppo_board = board.w
        else:
            my_board = board.w
            my_not_board = board.not_w
            oppo_board = board.b

        occuppied_zone = my_board + my_not_board
        possible_moves_tmp = my_board.copy()
        for i in range(self.search_range[0]):
            possible_moves_tmp = possible_moves_tmp + np.roll(my_board, i+1, axis=0)
            possible_moves_tmp = possible_moves_tmp + np.roll(my_board, -(i+1), axis=0)
        possible_moves = possible_moves_tmp.copy()
        for i in range(self.search_range[0]):
            possible_moves = possible_moves + np.roll(possible_moves_tmp, i+1, axis=1)
            possible_moves = possible_moves + np.roll(possible_moves_tmp, -(i+1), axis=1)
        possible_moves_tmp = oppo_board.copy()
        for i in range(self.search_range[1]):
            possible_moves_tmp = possible_moves_tmp + np.roll(oppo_board, i+1, axis=0)
            possible_moves_tmp = possible_moves_tmp + np.roll(oppo_board, -(i+1), axis=0)
        possible_moves = possible_moves + possible_moves_tmp
        for i in range(self.search_range[1]):
            possible_moves = possible_moves + np.roll(possible_moves_tmp, i+1, axis=1)
            possible_moves = possible_moves + np.roll(possible_moves_tmp, -(i+1), axis=1)
        all_move_board = possible_moves * (occuppied_zone == 0)
        valid = np.where(all_move_board > 0)
        return list(zip(valid[0], valid[1]))

    def _sort_possible_moves(self, board, possible_moves):
        val = []
        for each in possible_moves:
            board.move(each, is_dest_padded=True)
            val.append(self.value_board.get_board_val(board, not board.is_b))
            board.revert_move()
        combo = list(zip(val, possible_moves))
        combo.sort(key=lambda x:x[0], reverse=True)
        return [x[1] for x in combo], [x[0] for x in combo]

class valueBoard:
    """Value the board and make it efficient"""
    def __init__(self):
        self.shape_value_self = SHAPE_VALUE_SELF
        self.shape_value_oppo = SHAPE_VALUE_OPPO
        self._init_val_hash() # val_hash: value of each five line. BOARD_MAP numpy array to quickly take all the five lines from a board.

    def _init_val_hash(self, path = PATH_VAL_HASH):
        """Generate the value hash to evaluate the board values"""
        try:
            with open(path, "rb") as fin:
                self.val_hash = pickle.load(fin)
                self.BOARD_MAP
                if True == IS_DEBUG:
                    print("Loaded value hash board map from "+path)
                return
        except:
            if True == IS_DEBUG:
                print("Generating value hash...")
        self.val_hash = self._gen_val_hash()
        self.BOARD_MAP = self._gen_board_map()
        if True == IS_SAVE_CACHE:
            if True == IS_DEBUG:
                print("Saving value hash and board map to " +path)
            with open(path, "wb") as fout:
                pickle.dump(self.val_hash, fout)
                pickle.dump(self.BOARD_MAP, fout)

    def _gen_val_hash(self):
        val_hash = dict()
        for each_line_shape in itertools.product([-1, 0, 1], repeat=VALUE_WINDOW):
            key = encode_line_embedded(np.array(each_line_shape, dtype=int))
            val_hash[key] = self._eval_line(each_line_shape)
        return val_hash

    def _eval_line(self, line_shape):
        num_my_piece = line_shape.count(1)
        num_oppo_piece = line_shape.count(-1)
        if num_my_piece > 0 and num_oppo_piece > 0:
            return 0
        else:
            return self.shape_value_self[num_my_piece] - self.shape_value_oppo[num_oppo_piece]

    def _gen_board_map(self):
        board_map = []
        LEN_PADDED_BORAD_ROW = 2 * PAD_SIZE + BOARD_SIZE
        # heng
        for i in range(PAD_SIZE, PAD_SIZE + BOARD_SIZE):
            for j in range(PAD_SIZE, PAD_SIZE + BOARD_SIZE - VALUE_WINDOW + 1):
                board_map.append([LEN_PADDED_BORAD_ROW * i + m for m in range(j, j + VALUE_WINDOW)])
                # print([(i-PAD_SIZE, m-PAD_SIZE) for m in range(j, j+VALUE_WINDOW)])
        # shu
        for j in range(PAD_SIZE, PAD_SIZE + BOARD_SIZE):
            for i in range(PAD_SIZE, PAD_SIZE + BOARD_SIZE - VALUE_WINDOW + 1):
                board_map.append([LEN_PADDED_BORAD_ROW * m + j for m in range(i, i + VALUE_WINDOW)])
                # print([ (m-PAD_SIZE, j-PAD_SIZE) for m in range(i, i + VALUE_WINDOW)])
        # pie
        for j in range(PAD_SIZE + VALUE_WINDOW - 1, PAD_SIZE + BOARD_SIZE): # including the main diagnal
            for i in range(PAD_SIZE, j - (VALUE_WINDOW - 1) + 1):
                board_map.append([LEN_PADDED_BORAD_ROW * m + (j - (m - PAD_SIZE)) for m in range(i, i + VALUE_WINDOW)])
                # print([(m-PAD_SIZE, (j - (m - PAD_SIZE)) - PAD_SIZE) for m in range(i, i+VALUE_WINDOW)])
        for j in range(PAD_SIZE + 1, PAD_SIZE + BOARD_SIZE - (VALUE_WINDOW - 1)):
            for i in range(j, PAD_SIZE + BOARD_SIZE - (VALUE_WINDOW - 1)):
                board_map.append([LEN_PADDED_BORAD_ROW * m + (PAD_SIZE+BOARD_SIZE-1 - (m-j)) for m in range(i, i + VALUE_WINDOW)])
                # print([ (m-PAD_SIZE, (PAD_SIZE+BOARD_SIZE-1 - (m-j))-PAD_SIZE) for m in range(i, i + VALUE_WINDOW)])
        # na
        for j in range(PAD_SIZE + VALUE_WINDOW - 1, PAD_SIZE + BOARD_SIZE):
            for i in range(PAD_SIZE + BOARD_SIZE - 1 - (j - PAD_SIZE), PAD_SIZE + BOARD_SIZE -(VALUE_WINDOW - 1)):
                board_map.append([LEN_PADDED_BORAD_ROW * m + (j - (PAD_SIZE + BOARD_SIZE - 1 - m)) for m in range(i, i + VALUE_WINDOW)])
                # print([ (m-PAD_SIZE, (j - (PAD_SIZE + BOARD_SIZE - 1 - m))-PAD_SIZE) for m in range(i, i + VALUE_WINDOW)])
        for j in range(PAD_SIZE + 1, PAD_SIZE + BOARD_SIZE - (VALUE_WINDOW - 1)):
            for i in range(PAD_SIZE, PAD_SIZE + BOARD_SIZE - (j - PAD_SIZE) - (VALUE_WINDOW - 1)):
                board_map.append([LEN_PADDED_BORAD_ROW * m + j + m - PAD_SIZE for m in range(i, i+VALUE_WINDOW)])
                # print([(m - PAD_SIZE, j + m - PAD_SIZE - PAD_SIZE) for m in range(i, i+VALUE_WINDOW)])
        return np.array(board_map, dtype=int)

    def get_board_val(self, board, is_b):
        if True == is_b:
            my_board = board.b
            oppo_board = board.w
        else:
            my_board = board.w
            oppo_board = board.b

        value_board = my_board - oppo_board
        shape = value_board.take(self.BOARD_MAP)
        # res = 0
        # for each in shape:
        #     res += self.val_hash[encode_line_embedded(each)]
        res_list = map(self.get_val_hash, shape)
        res = sum(res_list)

        return res/board.current_round

    def get_val_hash(self, key):
        return self.val_hash[encode_line_embedded(key)]


if __name__ == "__main__":
    # start = time.time()
    # val = valueBoard()
    # import board
    # board = board.board()
    # ai = absearch()
    # moves = [(7,7), (8,8), (7,6), (8,5), (7, 8)]
    # res = ai._find_all_moves(board)
    # print(res)
    # for move in moves:
    #     board.move(move)
    #     res = ai._find_all_moves(board)
    #     print("possible moves")
    #     print(res)
    #     res = ai.get_strategy(board)
    #     print("Strategy")
    #     print(res)

    # print("Total time", time.time()-start)

    val = valueBoard()
