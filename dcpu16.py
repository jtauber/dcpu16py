#!/usr/bin/env python


import inspect
import struct
import sys
import argparse

try:
    raw_input
except NameError:
    raw_input = input

# offsets into DCPU16.memory corresponding to addressing mode codes
SP, PC, O = 0x1001B, 0x1001C, 0x1001D


def opcode(code):
    """A decorator for opcodes"""
    def decorator(func):
        setattr(func, "_is_opcode", True)
        setattr(func, "_opcode", code)
        return func
    
    return decorator


class DCPU16:
    
    def __init__(self, memory):
        self.memory = [memory[i] if i < len(memory) else 0 for i in range(0x1001E)]
        self.skip = False
        self.cycle = 0
        
        self.debugger_breaks = set()
        self.debugger_in_continue = False
        
        self.opcodes = {}
        for name, value in inspect.getmembers(self):
            if inspect.ismethod(value) and getattr(value, "_is_opcode", False):
                self.opcodes[getattr(value, "_opcode")] = value 
    
    @opcode(0x01)
    def SET(self, a, b):
        self.memory[a] = b
        self.cycle += 1
    
    @opcode(0x02)
    def ADD(self, a, b):
        o, r = divmod(self.memory[a] + b, 0x10000)
        self.memory[O] = o
        self.memory[a] = r
        self.cycle += 2
    
    @opcode(0x03)
    def SUB(self, a, b):
        o, r = divmod(self.memory[a] - b, 0x10000)
        self.memory[O] = 0xFFFF if o == -1 else 0x0000
        self.memory[a] = r
        self.cycle += 2
    
    @opcode(0x04)
    def MUL(self, a, b):
        o, r = divmod(self.memory[a] * b, 0x10000)
        self.memory[a] = r
        self.memory[O] = o % 0x10000
        self.cycle += 2
    
    @opcode(0x05)
    def DIV(self, a, b):
        if b == 0x0:
            r = 0x0
            o = 0x0
        else:
            r = self.memory[a] / b % 0x10000
            o = ((self.memory[a] << 16) / b) % 0x10000
        self.memory[a] = r
        self.memory[O] = o
        self.cycle += 3
    
    @opcode(0x06)
    def MOD(self, a, b):
        if b == 0x0:
            r = 0x0
        else:
            r = self.memory[a] % b
        self.memory[a] = r
        self.cycle += 3
    
    @opcode(0x07)
    def SHL(self, a, b):
        r = self.memory[a] << b
        o = ((self.memory[a] << b) >> 16) % 0x10000
        self.memory[a] = r
        self.memory[O] = o
        self.cycle += 2
    
    @opcode(0x08)
    def SHR(self, a, b):
        r = self.memory[a] >> b
        o = ((self.memory[a] << 16) >> b) % 0x10000
        self.memory[a] = r
        self.memory[O] = o
        self.cycle += 2
    
    @opcode(0x09)
    def AND(self, a, b):
        self.memory[a] = self.memory[a] & b
        self.cycle += 1
    
    @opcode(0x0a)
    def BOR(self, a, b):
        self.memory[a] = self.memory[a] | b
        self.cycle += 1
    
    @opcode(0x0b)
    def XOR(self, a, b):
        self.memory[a] = self.memory[a] ^ b
        self.cycle += 1
    
    @opcode(0x0c)
    def IFE(self, a, b):
        self.skip = not (self.memory[a] == b)
        self.cycle += 2 + 1 if self.skip else 0
    
    @opcode(0x0d)
    def IFN(self, a, b):
        self.skip = not (self.memory[a] != b)
        self.cycle += 2 + 1 if self.skip else 0
    
    @opcode(0x0e)
    def IFG(self, a, b):
        self.skip = not (self.memory[a] > b)
        self.cycle += 2 + 1 if self.skip else 0
    
    @opcode(0x0f)
    def IFB(self, a, b):
        self.skip = not ((self.memory[a] & b) != 0)
        self.cycle += 2 + 1 if self.skip else 0
    
    @opcode(0x010)
    def JSR(self, a, b):
        self.memory[SP] = (self.memory[SP] - 1) % 0x10000
        pc = self.memory[PC]
        self.memory[self.memory[SP]] = pc
        self.memory[PC] = b
        self.cycle += 2
    
    def get_operand(self, a, dereference=False):
        literal = False
        if a < 0x08 or 0x1B <= a <= 0x1D:
            arg1 = 0x10000 + a
        elif a < 0x10:
            arg1 = self.memory[0x10000 + (a % 0x08)]
        elif a < 0x18:
            next_word = self.memory[self.memory[PC]]
            self.memory[PC] += 1
            arg1 = next_word + self.memory[0x10000 + (a % 0x10)]
            self.cycle += 1
        elif a == 0x18:
            arg1 = self.memory[SP]
            self.memory[SP] = (self.memory[SP] + 1) % 0x10000
        elif a == 0x19:
            arg1 = self.memory[SP]
        elif a == 0x1A:
            self.memory[SP] = (self.memory[SP] - 1) % 0x10000
            arg1 = self.memory[SP]
        elif a == 0x1E:
            arg1 = self.memory[self.memory[PC]]
            self.memory[PC] += 1
            self.cycle += 1
        elif a == 0x1F:
            arg1 = self.memory[PC]
            self.memory[PC] += 1
            self.cycle += 1
        else:
            literal = True
            arg1 = a % 0x20
        
        if dereference and not literal:
            arg1 = self.memory[arg1]
        return arg1
    
    def run(self, debug=False, trace=False):
        while True:
            pc = self.memory[PC]
            w = self.memory[pc]
            self.memory[PC] += 1
            
            operands, opcode = divmod(w, 16)
            b, a = divmod(operands, 64)
            
            if trace:
                print("(%08X) %04X: %04X" % (self.cycle, pc, w))
            
            if opcode == 0x00:
                arg1 = None
                opcode = (a << 4) + 0x0
            else:
                arg1 = self.get_operand(a)
            
            op = self.opcodes[opcode]
            arg2 = self.get_operand(b, dereference=True)
            
            if self.skip:
                if trace:
                    print("skipping")
                self.skip = False
            else:
                op(arg1, arg2)
                if 0x01 <= opcode <=0xB:
                    if 0x8000 <= arg1 <= 0x8FFF:
                        self.update_video(arg1)
                if trace:
                    self.dump_registers()
                    self.dump_stack()
            
            if debug:
                self.debugger_prompt()
    
    def debugger_prompt(self):
        if not self.debugger_in_continue or self.memory[PC] in self.debugger_breaks:
            self.debugger_in_continue = False
            while True:
                try:
                    command = [s.lower() for s in raw_input("debug> ").split()]
                except EOFError:
                    # Ctrl-D
                    print("")
                    sys.exit()
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
                        if len(command) < 2:
                            raise ValueError("Clear command takes at least 1 parameter!")
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
                return  (PC, SP, O)[specials.index(what)]
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
        self.memory[addr] = value
    
    def debugger_get(self, what):
        addr = self.debugger_parse_location(what)
        value = self.memory[addr]
        print("hex: {hex}\ndec: {dec}\nbin: {bin}".format(hex=hex(value), dec=value, bin=bin(value)))
    
    def dump_registers(self):
        print(" ".join("%s=%04X" % (["A", "B", "C", "X", "Y", "Z", "I", "J"][i],
            self.memory[0x10000 + i]) for i in range(8)))
        print(" ".join("%s=%04X" % (["PC", "SP", "O"][i - PC],
            self.memory[i]) for i in [PC, SP, O]))
    
    def dump_stack(self):
        if self.memory[SP] == 0x0:
            print("Stack: []")
        else:
            print("Stack: [" + " ".join("%04X" % self.memory[m] for m in range(self.memory[SP], 0x10000)) + "]")
    
    def update_video(self, location):
        print("%04X: %04X" % (location, self.memory[location]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DCPU-16 emulator")
    parser.add_argument("-d", "--debug", action="store_const", const=True, default=False, help="Run emulator in debug mode. This implies '--trace'")
    parser.add_argument("-t", "--trace", action="store_const", const=True, default=False, help="Print dump of registers and stack after every step")
    parser.add_argument("object_file", help="File with assembled DCPU binary")
    args = parser.parse_args()
    if args.debug:
        args.trace = True
    
    program = []
    with open(args.object_file, "rb") as f:
        word = f.read(2)
        while word:
            program.append(struct.unpack(">H", word)[0])
            word = f.read(2)
    
    dcpu16 = DCPU16(program)
    dcpu16.run(debug=args.debug, trace=args.trace)
