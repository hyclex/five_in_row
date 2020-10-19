import numpy as np
import pickle
from config import *
if True == IS_DEBUG:
    import search
import os

class board:
    def __init__(self, moves=None):
        self.SIZE = BOARD_SIZE
        self.PAD_SIZE = PAD_SIZE
        self.PER_PIECE_VIEW_RANGE = PER_PIECE_VIEW_RANGE

        self.reset_board()
        if None == moves:
            self.moves = [None] * self.SIZE * self.SIZE
        else:
            self.moves = moves
        self._init_aug_nums() # LINE_NAMES, LINE_REL_POS, LINE_ABS_POS
        self._init_move_hash() # move_hash
# for debug purpose
        if True == IS_DEBUG:
            self.value = search.valueBoard()
# end for debug perpose

    def reset_board(self):
        self.b = np.zeros([self.SIZE+2*PAD_SIZE, self.SIZE+2*PAD_SIZE], dtype=int)
        self.not_b = np.ones([self.SIZE+2*PAD_SIZE, self.SIZE+2*PAD_SIZE], dtype=int)
        self.not_b[PAD_SIZE : PAD_SIZE+self.SIZE, PAD_SIZE : PAD_SIZE+self.SIZE] = 0
        self.w = np.zeros([self.SIZE+2*PAD_SIZE, self.SIZE+2*PAD_SIZE], dtype=int)
        self.not_w = np.ones([self.SIZE+2*PAD_SIZE, self.SIZE+2*PAD_SIZE], dtype=int)
        self.not_w[PAD_SIZE : PAD_SIZE+self.SIZE, PAD_SIZE : PAD_SIZE+self.SIZE] = 0

        self.current_round = 0
        self.is_b = True
        self.status = 0 # 0 runing, 1: black won, 2: white won, 3: draw

    def dest_to_padded_dest(self, dest):
        return (dest[0]+PAD_SIZE, dest[1]+PAD_SIZE)
    def padded_dest_to_dest(self, padded_dest):
        return (padded_dest[0]-PAD_SIZE, padded_dest[1]-PAD_SIZE)

    def get_b(self, dest):
        padded_dest = self.dest_to_padded_dest(dest)
        return self.b[padded_dest]
    def get_w(self, dest):
        padded_dest = self.dest_to_padded_dest(dest)
        return self.w[padded_dest]

    def move(self, dest, is_dest_padded=False):
        """Main move funtion. Input the true dest index. """
        try: 
            assert isinstance(dest, tuple)
        except:
            dest = tuple(dest)
        if False == is_dest_padded:
            padded_dest = self.dest_to_padded_dest(dest)
        else:
            padded_dest = dest
        if False == self.is_padded_move_valid(padded_dest):
            return 1
        if True == self.is_b:
            self.b[padded_dest] = 1
            self.not_w[padded_dest] = 1
        else:
            self.w[padded_dest] = 1
            self.not_b[padded_dest] = 1
        self.moves[self.current_round] = padded_dest
        self.current_round += 1
        self.is_b = not self.is_b
# for debug purpose
        if True == IS_DEBUG:
            list_type, list_must_move = self.move_status()
            print("\nRound", self.current_round-1, "Move", padded_dest)
            str_move = ""
            for each in list_type:
                str_move += " " + Shape.NAMES[each]
            print("type of last move: ", str_move)
            print("must move pos are: ", list_must_move)
            print("is win? ", self._is_win_advanced(list_type, list_must_move))
            print("board value: ", self.value.get_board_val(self, not self.is_b))
# end of debug module
        return 0

    def is_padded_move_valid(self, padded_dest):
        return not (self.b[padded_dest] or self.w[padded_dest])

    def revert_move(self):
        try:
            padded_dest = self.get_last_move()
            if False == self.is_b:
                self.b[padded_dest] = 0
                self.not_w[padded_dest] = 0
            else:
                self.w[padded_dest] = 0
                self.not_b[padded_dest] = 0
            self.current_round -= 1
            self.is_b = not self.is_b
        except:
            pass

    def _is_win_naive(self):
        """Simply judge by whether no less than 5 pieces are in a line"""
        if False == self.is_b:
            my_board = self.b
        else:
            my_board = self.w
        last_move = self.get_last_move()
        critical_line = self._get_critical_line(last_move, my_board)

        for each in critical_line:
            left = PER_PIECE_VIEW_RANGE
            right = PER_PIECE_VIEW_RANGE
            while each[left] == 1:
                left -= 1
            while each[right] == 1:
                right += 1
            if right - left - 1 >= 5:
                return True
        return False

    def _is_win_advanced(self, list_type=None, list_must_move=None):
        """Consider typical shapes of win, but does not consider the forbidden move"""
        if None == list_type and None == list_must_move:
            list_type, list_must_move = self.move_status()
        if Shape.WU in list_type or Shape.CHANGLIAN in list_type:
            return 2
        if len(list_must_move) >= 2:
            return 1
        if len(list_must_move) == 1 and len(list_type) >= 2:
            return 1
        if Shape.HUOSI in list_type:
            return 1
        return 0

    def _is_win_with_forbidden(self):
        """judge whther black did forbidden move
        If black moves, first judge whether black lost. Then we do a simple naive check. 
        """
        pass

    def update_game_status(self):
        # 0: runing, 1: b won, 2 w won by five, 3: w won by black forbidden (TO DO), 4: draw 
        ## to do, adding forbidden move, first judge whether black losses
        if True == self._is_win_naive(): 
            if False == self.is_b:
                self.status = 1
                return 1
            else:
                self.status = 2
                return 2 
        else:
            if self.current_round == self.SIZE * self.SIZE:
                self.status = 4
                return 4 # draw 
            else:
                return 0 # not end

    def get_last_move(self, is_padded=True):
        if True == is_padded:
            return self.moves[self.current_round-1]
        else:
            return self.padded_dest_to_dest(self.moves[self.current_round-1])


    def _init_move_hash(self, path=PATH_MOVE_HASH):
        try:
            with open(path, "rb") as fin:
                self.move_hash = pickle.load(fin)
                if True == IS_DEBUG:
                    print("Loaded move hash from "+path)
                return
        except:
            if True == IS_DEBUG:
                print("Generating move hash...")
        self.move_hash = MoveHash.gen_last_move_hash()

    def _init_aug_nums(self):
        """Prepare the relative position numbers for get_line_key_around_piece"""
        self.LINE_NAMES = ["heng", "shu", "pie", "na"]
        self.LINE_REL_POS = [None] * 4
        self.LINE_REL_POS[0] = [i for i in range(-PER_PIECE_VIEW_RANGE, PER_PIECE_VIEW_RANGE+1)] # heng
        self.LINE_REL_POS[1] = [i * (self.SIZE+2*PAD_SIZE) for i in range(-PER_PIECE_VIEW_RANGE, PER_PIECE_VIEW_RANGE+1)] # shu
        self.LINE_REL_POS[2] = [i * (self.SIZE+2*PAD_SIZE-1)for i in range(-PER_PIECE_VIEW_RANGE, PER_PIECE_VIEW_RANGE+1)] # pie
        self.LINE_REL_POS[3] = [i * (self.SIZE+2*PAD_SIZE+1)for i in range(-PER_PIECE_VIEW_RANGE, PER_PIECE_VIEW_RANGE+1)] # na

        self.LINE_ABS_POS = [None] * 4
        self.LINE_ABS_POS[0] = [(0, i) for i in range(-PER_PIECE_VIEW_RANGE, PER_PIECE_VIEW_RANGE+1)] # heng
        self.LINE_ABS_POS[1] = [(i, 0) for i in range(-PER_PIECE_VIEW_RANGE, PER_PIECE_VIEW_RANGE+1)] # shu
        self.LINE_ABS_POS[2] = [(i, -i) for i in range(-PER_PIECE_VIEW_RANGE, PER_PIECE_VIEW_RANGE+1)] # pie
        self.LINE_ABS_POS[3] = [(i, i) for i in range(-PER_PIECE_VIEW_RANGE, PER_PIECE_VIEW_RANGE+1)] # na

    def get_abs_position(self, padded_dest, relative_move_in_line):
        '''Get the absolute board coordinate of the moves in relative position around a dest
        ralative_move_in_line contains 4 list, each is the relative position of heng, shu, pie, na respectively. The order is critical. 
        '''
        position = []
        for rel_pos, pos_map in zip(relative_move_in_line, self.LINE_ABS_POS):
            for each_pos in rel_pos:
                if each_pos != None:  # None is the flag of a case without a must move
                    position.append((padded_dest[0]+pos_map[each_pos][0], padded_dest[1]+pos_map[each_pos][1]))
        return position

    def _get_critical_line(self, padded_dest, board_name):
        '''Get the board values of the cirtical lines around the dest'''
        line = list()
        padded_dest_pos = (self.SIZE+2*PAD_SIZE) * padded_dest[0] + padded_dest[1]
        for each in self.LINE_REL_POS:
            line.append(board_name.take([tmp+padded_dest_pos for tmp in each]))
        return line

    def get_critical_line_key(self, padded_dest, is_b):
        if True == is_b:
            my_board = self.b
            oppo_board = self.not_b
        else:
            my_board = self.w
            oppo_board = self.not_w
        line_key = list()
        list_my_line = self._get_critical_line(padded_dest, my_board)
        list_oppo_line = self._get_critical_line(padded_dest, oppo_board)
        for each_my_line, each_oppo_line in zip(list_my_line, list_oppo_line):
            line_key.append(encode_line(each_my_line, each_oppo_line))
        return line_key

    def move_status(self, padded_dest=None, is_b=None):
        """Evaluate the move status around some position"""
        if None == padded_dest and None == is_b:
            padded_dest = self.get_last_move()
            is_b = not self.is_b
        line_key = self.get_critical_line_key(padded_dest, is_b)
        list_type = list()
        list_must_move_rel = list()
        for each_line in line_key:
            list_type_tmp, list_must_move_tmp = self.move_hash[each_line]
            list_type.extend(list_type_tmp)
            list_must_move_rel.append(list_must_move_tmp)

        list_must_move_abs = self.get_abs_position(padded_dest, list_must_move_rel)
        return list_type, list_must_move_abs

    def encode_board(self):
        return (self.b[PAD_SIZE:PAD_SIZE+BOARD_SIZE, PAD_SIZE:PAD_SIZE+BOARD_SIZE] - self.w[PAD_SIZE:PAD_SIZE+BOARD_SIZE, PAD_SIZE:PAD_SIZE+BOARD_SIZE]).tostring()

    def save(self, folder="res", name=None):
        if name==None:
            name="last_game"
        with open(os.path.join(folder, name), "w") as fout:
            for i in range(self.current_round):
                fout.write(str(self.moves[i]))

class MoveHash:
    """
    for effective check about the last moving shape. pre calculate all the combination of shapes. when gaming running, simply check the state by finding the pre computed result in the hash table
    """
    def gen_last_move_hash(path=PATH_MOVE_HASH):
        import itertools
        """line_key => ((list of types), (move to break SI), [(move to break HUOSAN)"""
        move_hash = dict()
        for each_line_shape in itertools.product([-1, 0, 1], repeat=PER_PIECE_VIEW_RANGE*2):
            each_line_shape = list(each_line_shape)
            each_line_shape.insert(PER_PIECE_VIEW_RANGE, 1)
            key = encode_line_embedded(np.array(each_line_shape, dtype=int))
            move_hash[key] = MoveHash._eval_line(each_line_shape)

        # if True == IS_SAVE_CACHE:
        #     if True == IS_DEBUG:
        #         print("Saving move hash to " + path)
        #     with open(path, "wb") as fout:
        #         pickle.dump(move_hash, fout)
        return move_hash

    def _eval_line(line):
        left = PER_PIECE_VIEW_RANGE
        right = PER_PIECE_VIEW_RANGE
        list_type = list()  # refer class shape for types
        list_must_move = list() # moves that break the Shape.*_CHONGSI

        ## search for the largest connect
        while left >= 0 and line[left] == 1:
            left -= 1
        while right < 2 * PER_PIECE_VIEW_RANGE + 1 and line[right] == 1:
            right += 1
        num_connected = right - left - 1
        ## deal with the shape cases by case
        if num_connected > 5:
            list_type.append(Shape.CHANGLIAN)
            list_must_move.append(None)
            # end case connected > 5
        elif num_connected == 5:
            list_type.append(Shape.WU)
            list_must_move.append(None)
            # end case connected 5
        elif num_connected == 4:
            list_type_tmp, list_must_move_tmp = MoveHash._eval_line_c4(line, left, right)
            list_type.extend(list_type_tmp)
            list_must_move.extend(list_must_move_tmp)
            # end case connected 4
        elif num_connected == 3:
            list_type_tmp, list_must_move_tmp = MoveHash._eval_line_c3(line, left, right)
            list_type.extend(list_type_tmp)
            list_must_move.extend(list_must_move_tmp)
            # end case connected 3
        elif num_connected == 2:
            list_type_tmp, list_must_move_tmp = MoveHash._eval_line_c2(line, left, right)
            list_type.extend(list_type_tmp)
            list_must_move.extend(list_must_move_tmp)
            # end case connected 2
        elif num_connected == 1:
            list_type_tmp, list_must_move_tmp = MoveHash._eval_line_c1(line, left, right)
            list_type.extend(list_type_tmp)
            list_must_move.extend(list_must_move_tmp)
            # end case connected 1
        return tuple([tuple(list_type), tuple(list_must_move)])
        # end _eval_line

    def _eval_line_c4(line, left, right):
        list_type = list() 
        list_must_move = list() 

        if line[left] == 0:
            list_must_move.append(left)
            if line[left-1] == 1:
                list_type.append(Shape.TIAO_CHONGDUOSI)
            else:
                list_type.append(Shape.LIAN_CHONGSI)
        if line[right] == 0:
            list_must_move.append(right)
            if line[right+1] == 1:
                list_type.append(Shape.TIAO_CHONGDUOSI)
            else:
                list_type.append(Shape.LIAN_CHONGSI)
        # see if it is HUOSI
        if list_type.count(Shape.LIAN_CHONGSI) == 2:
            list_type = [Shape.HUOSI]
            list_must_move = [list_must_move[0]] # random fill a dest

        return list_type, list_must_move

    def _eval_line_c3(line, left, right):
        list_type = list()  
        list_must_move = list() 
        
        flag_huosan = True # track whether could be HUOSAN
        if line[left] == 0 and line[left-1] == 1:
            flag_huosan = False
            list_must_move.append(left)
            if line[left-2] == 1:
                list_type.append(Shape.TIAO_CHONGDUOSI)
            else:
                list_type.append(Shape.TIAO_CHONGSI)
        if line[right] == 0 and line[right+1] == 1:
            flag_huosan = False
            list_must_move.append(right)
            if line[right+2] == 1:
                list_type.append(Shape.TIAO_CHONGDUOSI)
            else:
                list_type.append(Shape.TIAO_CHONGSI)

        if True == flag_huosan and line[left] == 0 and line[right] == 0 and (line[left-1]==0 or line[right+1]==0):
            list_type.append(Shape.LIAN_HUOSAN)
            list_must_move.append(None)

        return list_type, list_must_move

    def _eval_line_c2(line, left, right):
        list_type = list() 
        list_must_move = list() 
        # check whether TIAO_CHONGSI or TIAO_CHONGDUOSI
        if line[left] == 0 and line[left-1] == 1 and line[left-2] == 1:
            list_must_move.append(left)
            if line[left-3] == 1:
                list_type.append(Shape.TIAO_CHONGDUOSI)
            else:
                list_type.append(Shape.TIAO_CHONGSI)
        if line[right] == 0 and line[right+1] == 1 and line[right+2] == 1:
            list_must_move.append(right)
            if line[right+3] == 1:
                list_type.append(Shape.TIAO_CHONGDUOSI)
            else:
                list_type.append(Shape.TIAO_CHONGSI)
        # check whether is TIAO_HUOSAN
        if line[left] == 0 and line[left-1] == 1 and line[left-2] == 0 and line[right] == 0 and line[left-3] != 1 and line[right+1] != 1:
            list_type.append(Shape.TIAO_HUOSAN)
            list_must_move.append(None)
        if line[right] == 0 and line[right+1] == 1 and line[right+2] == 0 and line[left] == 0 and line[right+3] !=1 and line[left-1] != 1:
            list_type.append(Shape.TIAO_HUOSAN)
            list_must_move.append(None)

        return list_type, list_must_move

    def _eval_line_c1(line, left, right):
        list_type = list()  # refer class shape for types
        list_must_move = list() # moves that break the Shape.*_CHONGSI
        # check whether is TIAO_CHONGDUOSI or TIAO_CHONGSI
        if line[left] == 0 and line[left-1] == 1 and line[left-2] == 1 and line[left-3] == 1:
            list_must_move.append(left)
            if line[left-4] == 1:
                list_type.append(Shape.TIAO_CHONGDUOSI)
            else:
                list_type.append(Shape.TIAO_CHONGSI)
        if line[right] == 0 and line[right+1] == 1 and line[right+2] == 1 and line[right+3] == 1:
            list_must_move.append(right)
            if line[right+4] == 1:
                list_type.append(Shape.TIAO_CHONGDUOSI)
            else:
                list_type.append(Shape.TIAO_CHONGSI)
        # check whether is TIAO_HUOSAN
        if line[left] == 0 and line[left-1] == 1 and line[left-2] == 1 and line[left-3] == 0 and line[right] == 0 and line[left-4] != 1 and line[right+1] != 1:
            list_type.append(Shape.TIAO_HUOSAN)
        if line[right] == 0 and line[right+1] == 1 and line[right+2] == 1 and line[right+3] == 0 and line[right+4] != 1 and line[left-1] != 1:
            list_type.append(Shape.TIAO_HUOSAN)
        return list_type, list_must_move

class Shape:
    NAMES = ["changlian", "wu", "huosi", "tiao_chongduosi", "lian_chongsi", "tiao_chongsi", "lian_huosan", "tiao_huosan", "lian_miansan", "tiao_miansan", "lian_huoer", "tiao1_huoer", "tiao2_huoer"]
    CHANGLIAN = 0
    WU = 1
    HUOSI = 2
    TIAO_CHONGDUOSI = 3
    LIAN_CHONGSI = 4
    TIAO_CHONGSI = 5
    LIAN_HUOSAN  = 6
    TIAO_HUOSAN = 7
    LIAN_MIANSAN = 8
    TIAO_MIANSAN = 9
    LIAN_HUOER = 10
    TIAO1_HUOER = 11
    TIAO2_HUOER = 12


if __name__ == "__main__":
    foo = board()
    val = search.valueBoard()
    moves = [(8,8), (1,1), (8,7), (1,2), (8,6), (8,5), (7,9), (2,2), (6,9), (2,3), (8,9)]
    for move in moves:
        foo.move(move)
        list_type, list_must_move = foo.move_status()
        print(move, val.get_board_val(foo, not foo.is_b))
