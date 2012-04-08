WIDTH = 32
HEIGHT = 16

class Terminal:
    width = WIDTH
    height = HEIGHT
    
    def __init__(self, args):
        pass
    
    def update_character(self, row, column, character, color=None):
        print("TERMINAL (%d,%d:'%s') %s" % (column, row, chr(character), str(color)))
    
    def show(self):
        pass
    
    def redraw(self):
        pass
    
    def quit(self):
        pass
