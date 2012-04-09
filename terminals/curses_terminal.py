import sys
import curses

WIDTH = 40
HEIGHT = 24

class Terminal:
    style_bold = False
    
    def setup_colors(self):
        curses.start_color()
        curses.use_default_colors()
        self.colors = {}
        self.colors[(0, 0)] = 0
        self.colors[(7, 0)] = 0
        self.color_index = 1
        self.win.bkgd(curses.color_pair(0))
    
    def __init__(self, args):
        if args.debug:
            print("Curses conflicts with debugger")
            raise SystemExit
        self.win = curses.initscr()
        self.win.nodelay(1)
        curses.curs_set(0)
        curses.noecho()
        self.width = WIDTH
        self.height = HEIGHT
        self.keys = []
        self.setup_colors()
    
    def get_color(self, fg, bg):
        if (fg, bg) not in self.colors:
            curses.init_pair(self.color_index, fg, bg)
            self.colors[(fg, bg)] = self.color_index
            self.color_index += 1

        return self.colors[(fg, bg)]
    
    def update_character(self, row, column, character, color=None):
        try:
            pair = 0
            if color:
                pair = self.get_color(*color)
            color = curses.color_pair(pair)
            if self.style_bold:
                color |= curses.A_BOLD
            self.win.addch(row, column, character, color)
        except curses.error:
            pass
    
    def show(self):
        pass
    
    def updatekeys(self):
        try:
            while(True):
                char = self.win.getkey()
                if len(char) == 1:
                    self.keys.insert(0, ord(char))
        except curses.error:
            pass
    
    def redraw(self):
        self.win.refresh()
    
    def quit(self):
        curses.endwin()
