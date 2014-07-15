from emuplugin import BasePlugin
import dcpu16

try:
    raw_input
except NameError:
    # Python3 raw_input was renamed to input
    raw_input = input

class DebuggerPlugin(BasePlugin):
    """
        A plugin to implement a debugger
    """

    def __init__(self, args):
        """
            Enable debugger if args.debug is True
        """
        BasePlugin.__init__(self)
        self.loaded = args.debug
        self.debugger_breaks = set()
        self.debugger_in_continue = False

    def tick(self, cpu):
        self.cpu = cpu
        if not self.debugger_in_continue or cpu.memory[dcpu16.PC] in self.debugger_breaks:
            self.debugger_in_continue = False
            while True:
                try:
                    command = [s.lower() for s in raw_input("debug> ").split()]
                except EOFError:
                    # Ctrl-D
                    print("")
                    raise SystemExit
                try:
                    if not command or command[0] in ("step", "st"):
                        break
                    elif command[0] == "help":
                        help_msg = """Commands:
help
st[ep] - (or simply newline) - execute next instruction
g[et] <address>|%<register> - (also p[rint]) - print value of memory cell or register
s[et] <address>|%<register> <value_in_hex> - set value of memory cell or register to <value_in_hex>
b[reak] <address> [<address2>...] - set breakpoint at given addresses (to be used with 'continue')
cl[ear] <address> [<address2>...] - remove breakpoints from given addresses
c[ont[inue]] - run without debugging prompt until breakpoint is encountered

All addresses are in hex (you can add '0x' at the beginning)
Close emulator with Ctrl-D
"""
                        print(help_msg)
                    elif command[0] in ("get", "g", "print", "p"):
                        self.debugger_get(*command[1:])
                    elif command[0] in ("set", "s"):
                        self.debugger_set(*command[1:])
                    elif command[0] in ("break", "b"):
                        if len(command) < 2:
                            raise ValueError("Break command takes at least 1 parameter!")
                        self.debugger_break(*command[1:])
                    elif command[0] in ("clear", "cl"):
                        self.debugger_clear(*command[1:])
                    elif command[0] in ("continue", "cont", "c"):
                        self.debugger_in_continue = True
                        break
                    else:
                        raise ValueError("Invalid command!")
                except ValueError as ex:
                    print(ex)

    @staticmethod
    def debugger_parse_location(what):
        registers = "abcxyzij"
        specials = ("pc", "sp", "o")
        if what.startswith("%"):
            what = what[1:]
            if what in registers:
                return  0x10000 + registers.find(what)
            elif what in specials:
                return  (dcpu16.PC, dcpu16.SP, dcpu16.O)[specials.index(what)]
            else:
                raise ValueError("Invalid register!")
        else:
            addr = int(what, 16)
            if not 0 <= addr <= 0xFFFF:
                raise ValueError("Invalid address!")
            return addr

    def debugger_break(self, *addrs):
        breaks = set()
        for addr in addrs:
            addr = int(addr, 16)
            if not 0 <= addr <= 0xFFFF:
                raise ValueError("Invalid address!")
            breaks.add(addr)
        self.debugger_breaks.update(breaks)

    def debugger_clear(self, *addrs):
        if not addrs:
            self.debugger_breaks = set()
        else:
            breaks = set()
            for addr in addrs:
                addr = int(addr, 16)
                if not 0 <= addr <= 0xFFFF:
                    raise ValueError("Invalid address!")
                breaks.add(addr)
            self.debugger_breaks.difference_update(breaks)

    def debugger_set(self, what, value):
        value = int(value, 16)
        if not 0 <= value <= 0xFFFF:
            raise ValueError("Invalid value!")
        addr = self.debugger_parse_location(what)
        self.cpu.memory[addr] = value

    def debugger_get(self, what):
        addr = self.debugger_parse_location(what)
        value = self.cpu.memory[addr]
        print("hex: {hex}\ndec: {dec}\nbin: {bin}".format(hex=hex(value), dec=value, bin=bin(value)))

plugin = DebuggerPlugin
