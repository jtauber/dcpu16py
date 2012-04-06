from emuplugin import BasePlugin
import importlib

START_ADDRESS = 0x8000

class TerminalPlugin(BasePlugin):
    """
        A plugin to implement terminal selection
    """
    
    arguments = [(["--term"], dict(action="store", default="null", help="Terminal to use (e.g. null, pygame)"))]
    
    def tick(self, cpu):
        """
            Update the display every 100,000hz or always if debug is on
        """
        if self.i >= 100000:
            self.i = 0
        if self.debug or self.i % 1000 == 0:
            self.term.redraw()
        self.i += 1
    
    def memory_changed(self, cpu, address, value):
        """
            Inform the terminal that the memory is updated
        """
        if not (self.term.width and self.term.height):
            # Null terminal
            return
        if START_ADDRESS <= address <= START_ADDRESS + self.term.width * self.term.height:
            row, column = divmod(address - START_ADDRESS, self.term.width)
            ch = value % 0x0080
            fg = (value & 0x4000) >> 14 | (value & 0x2000) >> 12 | (value & 0x1000) >> 10
            bg = (value & 0x400) >> 10 | (value & 0x200) >> 8 | (value & 0x100) >> 6
            self.term.update_character(row, column, ch, (fg, bg))
    
    def shutdown(self):
        """
            Shutdown the terminal
        """
        self.term.quit()
    
    def __init__(self, args):
        """
            Create a terminal based on the term argument
        """
        BasePlugin.__init__(self)
        self.i = 0
        terminal = importlib.import_module(args.term + "_terminal")
        self.debug = args.debug
        self.term = terminal.Terminal()
        self.name += "-%s" % args.term
        self.term.show()

plugin = TerminalPlugin
