import wx
import board
from player import *
import os
from threading import *

# Define notification event for thread completion
EVT_RESULT_ID = wx.NewId()

def EVT_RESULT(win, func):
    """Define Result Event."""
    win.Connect(-1, -1, EVT_RESULT_ID, func)

class ResultEvent(wx.PyEvent):
    """Simple event to carry arbitrary result data."""
    def __init__(self, data=None):
        """Init Result Event."""
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_RESULT_ID)
        self.data = data

class ai_move_thread(Thread):
    """AI move threading, in order to reveal instant frame changes"""
    def __init__(self, main_frame):
        Thread.__init__(self)
        self.main_frame = main_frame
        self.start()

    def run(self):
        main = self.main_frame
        main.play_panel.game_status_text.SetLabel("Gaming is runing and AI is computing...")
        current_player = main.get_current_player()
        dest = current_player.get_strategy(main.board)
        main.board.move(dest)
        main.play_panel.refresh_text()
        main.play_panel.board_panel.update_piece(dest, main.board.get_b(dest), main.board.get_w(dest))
        main.board.update_game_status()
        main.play_panel.game_status_text.SetLabel("Game is running...")
        if main.board.status == 0:
            wx.PostEvent(main, ResultEvent())
        else:
            main.ending(main.board.status)

class MainFrame(wx.Frame):
    """Main control frame"""
    def __init__(self, parent, ID, title, pos=wx.DefaultPosition, style=wx.DEFAULT_FRAME_STYLE):
        wx.Frame.__init__(self, parent, ID, title, pos, (1000, 700), style)
        self.welcome_panel = WelcomePanel(self)

        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        self.main_sizer.Add(self.welcome_panel, 1, wx.EXPAND)
        self.SetSizer(self.main_sizer)

        self.Bind(wx.EVT_BUTTON, self.OnStart, self.welcome_panel.start_button)
        self.Connect(-1,-1, EVT_RESULT_ID, self.ai_move)

    def OnStart(self, event):
        # intial inner board infomation
        self.board = board.board()
        self.b_player = self._init_player(True, self.welcome_panel.b_player_setting.GetItemLabel(self.welcome_panel.b_player_setting.GetSelection()), self.welcome_panel.b_ai_setting.GetSelection())
        self.w_player = self._init_player(False, self.welcome_panel.w_player_setting.GetItemLabel(self.welcome_panel.w_player_setting.GetSelection()), self.welcome_panel.w_ai_setting.GetSelection())
        # display 
        if True == hasattr(self, "play_panel"):
            self.play_panel.refresh_text()
            self.play_panel.board_panel.reint_piece()
        else:
            self.play_panel = PlayPanel(self)
            self.main_sizer.Add(self.play_panel, 1, wx.EXPAND)
            self.Bind(wx.EVT_BUTTON, self.OnQuit, self.play_panel.quit_button)
            self.Bind(wx.EVT_BUTTON, self.OnRevert, self.play_panel.revert_button)
            self.play_panel.board_panel.board_bmp.Bind(wx.EVT_LEFT_DOWN, self.OnClick)

        self.welcome_panel.Hide()
        self.play_panel.Show()
        self.Layout()
        # start the move
        wx.PostEvent(self, ResultEvent())

    def ai_move(self, event):
        if self.board.status != 0 or self.get_current_player().type == "human":
            self.get_current_player().timer_tic()
            return
        self.ai_worker = ai_move_thread(self)

    def OnQuit(self, event):
        self.play_panel.Hide()
        self.welcome_panel.Show()
        self.Layout()

    def OnRevert(self, event):
        current_player = self.get_current_player()
        if current_player.type != "human":
            return

        self.board.status = 0
        if self.board.current_round > 0:
            dest = self.board.get_last_move(is_padded=False)
            self.board.revert_move()
            current_player.time_update()
            self.play_panel.refresh_text()
            self.play_panel.board_panel.update_piece(dest, 0, 0, False)
        if self.board.current_round > 0: # do it twice
            dest = self.board.get_last_move(is_padded=False)
            self.board.revert_move()
            current_player.time_update()
            self.play_panel.refresh_text()
            self.play_panel.board_panel.update_piece(dest, 0, 0, False)

        wx.PostEvent(self, ResultEvent())

    def OnClick(self, event):
        if self.board.status != 0:
            return
        current_player = self.get_current_player()
        if current_player.type != "human":
            return
        pos_x, pos_y = event.GetPosition()
        GRID_SIZE = self.play_panel.board_panel.GRID_SIZE
        if pos_x < GRID_SIZE * 0.5 or pos_x >= GRID_SIZE * (0.5 + self.board.SIZE) or pos_y < GRID_SIZE * 0.5 or pos_y >= GRID_SIZE * (0.5 + self.board.SIZE):
            return

        dest = self._pos_to_ind(pos_x, pos_y)
        move_stat = self.board.move(dest)
        if move_stat == 0:
            current_player.time_update()
            self.play_panel.refresh_text()
            self.play_panel.board_panel.update_piece(dest, self.board.get_b(dest), self.board.get_w(dest))
            self.board.update_game_status()

            if self.board.status > 0:
                self.ending(self.board.status) # ending
            else:
                wx.PostEvent(self, ResultEvent())

    def ending(self, status):
        if status == 1:
            res = "Black won. "
        elif status == 2:
            res = "White won. "
        elif status == 3:
            res = "White won due to black hit forbidden move. "
        else:
            res = "Draw game. "
        self.play_panel.game_status_text.SetLabel(res)


    def _init_player(self, is_b, player_type, ai_level):
        assert player_type in ["human", "ai"]
        if player_type == "human":
            return human_player(is_b, player_type)
        else:
            return ai_player(is_b, player_type, ai_level)

    def _pos_to_ind(self, pos_x, pos_y):
        GRID_SIZE = self.play_panel.board_panel.GRID_SIZE
        pos_x -= 0.5 * GRID_SIZE
        pos_y -= 0.5 * GRID_SIZE

        for i in range(self.board.SIZE):
            if pos_x <= (i+1) * GRID_SIZE:
                break
        for j in range(self.board.SIZE):
            if pos_y <= (j+1) * GRID_SIZE:
                break
        return (i, j)

    def get_current_player(self):
        if True == self.board.is_b:
            return  self.b_player
        else:
            return self.w_player


class WelcomePanel(wx.Panel):
    """Starting panel"""
    def __init__(self, parent):
        self.parent = parent
        wx.Panel.__init__(self, parent)
        self.main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        game_name = wx.StaticText(self, -1, "\nFive in Row", style=wx.ALIGN_CENTER)
        font_game_name = wx.Font(72, wx.DECORATIVE, wx.NORMAL, wx.BOLD)
        game_name.SetFont(font_game_name)
        self.main_sizer.Add(game_name, 1, wx.ALIGN_CENTER_HORIZONTAL)

        auther = wx.StaticText(self, -1, "By: Lex", style=wx.ALIGN_CENTER)
        self.main_sizer.Add(auther, 1, wx.ALIGN_CENTER_HORIZONTAL)

        self.PLAYTER_TYPE = ["human", "ai"]
        self.AI_LEVEL = ["random", "newbie", "good", "crazy"]

        self.b_player_setting = wx.RadioBox(self, -1, "Black Player: ", wx.DefaultPosition, wx.DefaultSize, self.PLAYTER_TYPE, 1, wx.RA_SPECIFY_ROWS)
        self.main_sizer.Add(self.b_player_setting, 0, wx.ALIGN_CENTER_HORIZONTAL)

        self.w_player_setting = wx.RadioBox(self, -1, "White Player: ", wx.DefaultPosition, wx.DefaultSize, self.PLAYTER_TYPE, 1, wx.RA_SPECIFY_ROWS)
        self.w_player_setting.SetSelection(1)
        self.main_sizer.Add(self.w_player_setting, 0, wx.ALIGN_CENTER_HORIZONTAL)

        self.b_ai_setting = wx.RadioBox(self, -1, "Black ai level: ", wx.DefaultPosition, wx.DefaultSize, self.AI_LEVEL, 1, wx.RA_SPECIFY_ROWS)
        self.b_ai_setting.SetSelection(2)
        self.main_sizer.Add(self.b_ai_setting, 0, wx.ALIGN_CENTER_HORIZONTAL)

        self.w_ai_setting = wx.RadioBox(self, -1, "White ai level: ", wx.DefaultPosition, wx.DefaultSize, self.AI_LEVEL, 1, wx.RA_SPECIFY_ROWS)
        self.w_ai_setting.SetSelection(2)
        self.main_sizer.Add(self.w_ai_setting, 0, wx.ALIGN_CENTER_HORIZONTAL)

        self.start_button = wx.Button(self, -1, "Start")
        self.main_sizer.Add(self.start_button, 1, wx.ALIGN_CENTER_HORIZONTAL)

        self.SetSizerAndFit(self.main_sizer)

class PlayPanel(wx.Panel):
    """Play panel"""
    def __init__(self, parent):
        self.parent = parent
        wx.Panel.__init__(self, parent)
        self.main_sizer = wx.BoxSizer(wx.HORIZONTAL)

        self.info_sizer = wx.BoxSizer(wx.VERTICAL)
        word_line1 = wx.StaticText(self, -1, "Current player: ")
        self.info_sizer.Add(word_line1, 0, wx.ALIGN_LEFT)

        self.current_player_text = wx.StaticText(self, -1, "Black")
        self.info_sizer.Add(self.current_player_text, 0, wx.ALIGN_LEFT | wx.BOTTOM, 20)

        self.b_player_status = wx.StaticText(self, -1, "Black player: "+self.parent.b_player.name+"\t"+self.parent.b_player.get_elapsed_time())
        self.info_sizer.Add(self.b_player_status, 0, wx.ALIGN_LEFT)

        self.w_player_status = wx.StaticText(self, -1, "White player: "+self.parent.w_player.name+"\t"+self.parent.w_player.get_elapsed_time())
        self.info_sizer.Add(self.w_player_status, 0, wx.ALIGN_LEFT | wx.BOTTOM, 20)

        self.game_status_text = wx.StaticText(self, -1, "Game is running...")
        self.info_sizer.Add(self.game_status_text, 0, wx.ALIGN_LEFT | wx.BOTTOM, 20)

        self.revert_button = wx.Button(self, -1, "Revert")
        self.quit_button = wx.Button(self, -1, "ToMain")
        button_bar_sizer = wx.BoxSizer(wx.HORIZONTAL)
        button_bar_sizer.Add(self.revert_button, 1, wx.ALIGN_LEFT)
        button_bar_sizer.Add(self.quit_button, 1, wx.ALIGN_LEFT)
        self.info_sizer.Add(button_bar_sizer, 0, wx.ALIGN_CENTER_HORIZONTAL)

        self.main_sizer.Add(self.info_sizer, 1, wx.ALIGN_LEFT | wx.ALL, 10)

        self.board_panel = BoardPanel(self)
        self.main_sizer.Add(self.board_panel, 1, wx.ALIGN_LEFT | wx.ALL, 10)

        self.SetSizerAndFit(self.main_sizer)

    def refresh_text(self):
        if True == self.parent.board.is_b:
            current_player_name = "Black"
        else:
            current_player_name = "White"
        self.current_player_text.SetLabel(current_player_name)
        self.b_player_status.SetLabel("Black player: "+self.parent.b_player.name+"\t"+self.parent.b_player.get_elapsed_time())
        self.w_player_status.SetLabel("White player: "+self.parent.w_player.name+"\t"+self.parent.w_player.get_elapsed_time())

        status = self.parent.board.status
        if status == 0:
            res = "Game is running"
        elif status == 1:
            res = "Black won. "
        elif status == 2:
            res = "White won. "
        else:
            res = "Draw game. "
        self.game_status_text.SetLabel(res)

class BoardPanel(wx.Panel):
    """Bitmap board panel"""
    def __init__(self, parent):
        self.root = parent.parent
        wx.Panel.__init__(self, parent)
        self.GRID_SIZE = 36 # pixel for each grid
        self.BOARD_SIZE = self.root.board.SIZE
        self._load_images()
        self.board_bmp = wx.StaticBitmap(self, -1, self.BOARD_BMP, (0,0))
        self.init_piece()

    def update_piece(self, pos, is_b, is_w, is_show=True):
        if is_b > 0:
            BMP = self.BLACK_BMP
        elif is_w > 0:
            BMP = self.WHITE_BMP
        else:
            BMP = self.BLANK_BMP
        self.piece_bmp[pos[0]][pos[1]].SetBitmap(BMP)
        if True == is_show:
            self.piece_bmp[pos[0]][pos[1]].Show()
        else:
            self.piece_bmp[pos[0]][pos[1]].Hide()

    def init_piece(self):
        self.piece_bmp = [[None] * self.BOARD_SIZE for i in range(self.BOARD_SIZE)]
        for i in range(self.BOARD_SIZE):
            for j in range(self.BOARD_SIZE):
                self.piece_bmp[i][j] = wx.StaticBitmap(self, -1, self.BLANK_BMP, (self.GRID_SIZE*(i+0.5), self.GRID_SIZE*(j+0.5)))
                self.piece_bmp[i][j].Hide()

    def reint_piece(self):
        for i in range(self.BOARD_SIZE):
            for j in range(self.BOARD_SIZE):
                self.update_piece((i,j), 0, 0, False)

    def _load_images(self, dir_path="dat"):
        self.BOARD_BMP = wx.Bitmap(os.path.join(dir_path, "board.bmp"))
        self.BLACK_BMP = wx.Bitmap(os.path.join(dir_path, "black.bmp"))
        self.WHITE_BMP = wx.Bitmap(os.path.join(dir_path, "white.bmp"))
        self.BLANK_BMP = wx.Bitmap(os.path.join(dir_path, "Null.bmp"))
        ## the following mask operation causes segmentation falt 11
        # mask = wx.Mask(self.BLACK_BMP, wx.WHITE)
        # self.BLACK_BMP.SetMask(mask)
        # self.WHITE_BMP.SetMask(mask)

if __name__ == "__main__":
    app = wx.App(False)
    frame = MainFrame(None, wx.ID_ANY, "Five in Row")
    frame.Show()
    app.MainLoop()