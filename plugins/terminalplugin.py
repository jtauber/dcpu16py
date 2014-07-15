from emuplugin import BasePlugin
import importlib
import sys
import time
import os
import re

START_ADDRESS = 0x8000
MIN_DISPLAY_HZ = 60


class TerminalPlugin(BasePlugin):
    """
        A plugin to implement terminal selection
    """

    arguments = [
        (["--term"], dict(action="store", default="null", help="Terminal to use (e.g. null, pygame)")),
        (["--geometry"], dict(action="store", default="80x24", help="Geometry given as `width`x`height`", metavar="SIZE"))]

    def processkeys(self, cpu):
        keyptr = 0x9000
        for i in range(0, 16):
            if not cpu.memory[keyptr + i]:
                try:
                    key = self.term.keys.pop()
                except IndexError:
                    break
                cpu.memory[keyptr + i] = key

    def tick(self, cpu):
        """
            Update the display every .1s or always if debug is on
        """
        if self.debug or not self.time or (time.time() - self.time >= 1.0 / float(MIN_DISPLAY_HZ)):
            self.time = time.time()
            self.term.redraw()
        self.term.updatekeys()
        if self.term.keys:
            self.processkeys(cpu)

    def memory_changed(self, cpu, address, value, oldval):
        """
            Inform the terminal that the memory is updated
        """
        if START_ADDRESS <= address <= START_ADDRESS + self.term.width * self.term.height:
            row, column = divmod(address - START_ADDRESS, self.term.width)
            ch = value % 0x0080
            ch = ord(' ') if not ch else ch
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
        if args.term == "null":
            self.loaded = False
            return
        BasePlugin.__init__(self)
        self.time = None
        sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "terminals")))
        try:
            terminal = importlib.import_module(args.term + "_terminal")
        except ImportError as e:
            print("Terminal %s not available: %s" % (args.term, e))
            raise SystemExit
        self.debug = args.debug

        m = re.match(r"(\d+)x(\d+)", args.geometry)
        if m is None:
            print("Invalid geometry `%s`" % args.geometry)
            args.width, args.height = 80, 24
        else:
            args.width = int(m.group(1))
            args.height = int(m.group(2))

        self.term = terminal.Terminal(args)
        self.name += "-%s" % args.term
        self.term.show()

plugin = TerminalPlugin
