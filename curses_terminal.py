import curses

WIDTH = 40
HEIGHT = 24
START_ADDRESS = 0x8000

class Terminal:

    def __init__(self):
        curses.initscr()
        self.win = curses.newwin(WIDTH, HEIGHT, 0, 0)
    
    def update_memory(self, address, value):
        if START_ADDRESS <= address <= START_ADDRESS + WIDTH * HEIGHT * 2:
            row, column = divmod(address - START_ADDRESS, WIDTH)
            self.win.addch(row, column, value)
    
    def show(self):
        pass
    
    def redraw(self):
        self.win.refresh()
    
    def quit(self):
        curses.endwin()
