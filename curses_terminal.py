import sys
import curses

WIDTH = 40
HEIGHT = 24
START_ADDRESS = 0x8000

class Terminal:

    def __init__(self):
        self.win = curses.initscr()
        curses.start_color()
        curses.use_default_colors()

        self.colors = {}
        self.colors[(0, 0)] = 0
        self.colors[(7, 0)] = 0
        self.colors[(3, 4)] = 1
        curses.init_pair(1, 3, 4)

        self.color_index = 2
        self.win.bkgd(curses.color_pair(0))

    def get_color(self, fg, bg):
        if (fg, bg) not in self.colors:
            curses.init_pair(self.color_index, fg, bg)
            self.colors[(fg, bg)] = self.color_index
            self.color_index += 1

        return self.colors[(fg, bg)]
    
    def update_memory(self, address, value):
        if START_ADDRESS <= address <= START_ADDRESS + WIDTH * HEIGHT * 2:
            row, column = divmod(address - START_ADDRESS, WIDTH)
            fg = (value & 0x4000) >> 14 | (value & 0x2000) >> 12 | (value & 0x1000) >> 10
            bg = (value & 0x400) >> 10 | (value & 0x200) >> 8 | (value & 0x100) >> 6
            try:
                pair = self.get_color(fg, bg)
                self.win.addch(row, column, value & 0x7f, curses.color_pair(pair))
            except:
                pass

    def show(self):
        pass
    
    def redraw(self):
        self.win.refresh()
    
    def quit(self):
        curses.endwin()
