import numpy as np

IS_DEBUG = False # switch of turning on debug ifo
IS_SAVE_CACHE = False # switch of whether dump the hash tables for next time usage

BOARD_SIZE = 15 # board size, should not be changed
assert BOARD_SIZE == 15
PER_PIECE_VIEW_RANGE = 5 # for move hash, how far the critical line ends
PAD_SIZE = 5 # how much to pad on the edge of the board
assert PAD_SIZE >= PER_PIECE_VIEW_RANGE
VALUE_WINDOW = 5 # size of the window to evaluate the board, 
assert VALUE_WINDOW == 5

PATH_MAP_HASH = "dat/move_hash" # path to save the move hash data
PATH_VAL_HASH = "dat/val_hash"

INF = 2 ** 25 # absolute largest int
# SHAPE_VALUE = np.array([0, 12, 15, 20, 30, INF], dtype=int) # for basic board value evaluations. value for 0, 1, 2, 3, 4, 5 pieces. Different from a traditional sense in the value process. 
SHAPE_VALUE_SELF = np.array([0, 1, 5, 10, 32, INF], dtype=int)
SHAPE_VALUE_OPPO = np.array([0, 1, 6, 12, 35, INF], dtype=int)
assert SHAPE_VALUE_SELF[0] == 0 and SHAPE_VALUE_SELF[-1] == INF
assert SHAPE_VALUE_OPPO[0] == 0 and SHAPE_VALUE_OPPO[-1] == INF
# encoders for lines
def encode_line(my_line, oppo_line):
    return (my_line-oppo_line).tostring()

def encode_line_embedded(line):
    return line.tostring()