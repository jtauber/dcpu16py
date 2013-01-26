import curses


class Terminal:
    style_bold = False
    keymap = {'A': 0x3, 'C': 0x2, 'D': 0x1}

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
        self.win_height, self.win_width = self.win.getmaxyx()

        curses.curs_set(0)
        curses.noecho()
        self.width = args.width
        self.height = args.height
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
        color = curses.color_pair(self.get_color(3, -1))

        if self.win_width > self.width:
            try:
                s = '.'*(self.win_width - self.width)
                for y in range(self.height):
                    self.win.addstr(y, self.width, s, color)
            except curses.error:
                pass

        if self.win_height > self.height:
            try:
                s = '.'*(self.win_width)
                for y in range(self.height, self.win_height):
                    self.win.addstr(y, 0, s, color)
            except curses.error:
                pass

    def updatekeys(self):
        try:
            # XXX: this is probably a bad place to check if the window has
            # resized but there is no other opportunity to do this
            win_height, win_width = self.win.getmaxyx()
            if win_height != self.win_height or win_width != self.win_width:
                self.win_height, self.win_width = win_height, win_width
                self.show()

            while(True):
                char = self.win.getkey()
                if len(char) == 1:
                    c = self.keymap[char] if char in self.keymap else ord(char)
                    self.keys.insert(0, c)
        except curses.error:
            pass

    def redraw(self):
        self.win.refresh()

    def quit(self):
        curses.endwin()
