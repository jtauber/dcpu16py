WIDTH = 80
HEIGHT = 24


class Terminal:
    width = WIDTH
    height = HEIGHT
    keys = []

    def __init__(self, args):
        pass

    def update_character(self, row, column, character, color=None):
        print("TERMINAL (%d,%d:'%s') %s" % (column, row, chr(character), str(color)))

    def show(self):
        pass

    def updatekeys(self):
        pass

    def redraw(self):
        pass

    def quit(self):
        pass
