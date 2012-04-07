START_ADDRESS = 0x8000
WIDTH = 32
HEIGHT = 16

class Terminal:
    
    def update_memory(self, address, value):
        if START_ADDRESS <= address <= START_ADDRESS + WIDTH * HEIGHT * 2:
            row, column = divmod(address - START_ADDRESS, WIDTH)
            print("TERMINAL %04X: %04X (%d,%d:%s)" % (address, value, column, row, chr(value % 0x80)))
    
    def show(self):
        pass
    
    def redraw(self):
        pass
    
    def quit(self):
        pass
