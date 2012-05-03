#!/usr/bin/env python

import argparse
import importlib
import inspect
import struct
import sys
import time
import emuplugin
import disasm


try:
    raw_input
except NameError:
    raw_input = input


# offsets into DCPU16.memory corresponding to addressing mode codes
SP, PC, O, LIT = 0x1001B, 0x1001C, 0x1001D, 0x1001E


def opcode(code):
    """A decorator for opcodes"""
    def decorator(func):
        setattr(func, "_is_opcode", True)
        setattr(func, "_opcode", code)
        return func
    
    return decorator


class DCPU16:
    
    def __init__(self, memory, plugins=[]):
        
        self.plugins = plugins
        
        self.memory = [memory[i] if i < len(memory) else 0 for i in range(0x1001F)]
        
        self.skip = False
        self.cycle = 0
        
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
        o, r = divmod(self.memory[a] << b, 0x10000)
        self.memory[a] = r
        self.memory[O] = o % 0x10000
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
            self.cycle += 0 if self.skip else 1
        elif a == 0x18:
            arg1 = self.memory[SP]
            if not self.skip:
                self.memory[SP] = (self.memory[SP] + 1) % 0x10000
        elif a == 0x19:
            arg1 = self.memory[SP]
        elif a == 0x1A:
            if not self.skip:
                self.memory[SP] = (self.memory[SP] - 1) % 0x10000
            arg1 = self.memory[SP]
        elif a == 0x1E:
            arg1 = self.memory[self.memory[PC]]
            self.memory[PC] += 1
            self.cycle += 0 if self.skip else 1
        elif a == 0x1F:
            arg1 = self.memory[PC]
            self.memory[PC] += 1
            self.cycle += 0 if self.skip else 1
        else:
            literal = True
            arg1 = a % 0x20
            if not dereference:
                self.memory[LIT] = arg1
                arg1 = LIT
        
        if dereference and not literal:
            arg1 = self.memory[arg1]
        return arg1
    
    def run(self, trace=False, show_speed=False):
        tick = 0
        last_time = time.time()
        last_cycle = self.cycle
        if trace:
            disassembler = disasm.Disassembler(self.memory)
        
        while True:
            pc = self.memory[PC]
            w = self.memory[pc]
            self.memory[PC] += 1
            
            operands, opcode = divmod(w, 16)
            b, a = divmod(operands, 64)
            
            if trace:
                disassembler.offset = pc
                print("(%08X) %s" % (self.cycle, disassembler.next_instruction()))
            
            if opcode == 0x00:
                if a == 0x00:
                    break
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
                if 0x01 <= opcode <=0xB: # write to memory
                    oldval = self.memory[arg1]
                    op(arg1, arg2)
                    val = self.memory[arg1]
                    if oldval != val:
                        for p in self.plugins:
                            p.memory_changed(self, arg1, val, oldval)
                else:
                    op(arg1, arg2)
                if trace:
                    self.dump_registers()
                    self.dump_stack()
            
            tick += 1
            if tick >= 100000:
                if show_speed:
                    print("%dkHz" % (int((self.cycle - last_cycle) / (time.time() - last_time)) / 1000))
                last_time = time.time()
                last_cycle = self.cycle
                tick = 0
            try:
                for p in self.plugins:
                    p.tick(self)
            except SystemExit:
                break
    
    def dump_registers(self):
        print(" ".join("%s=%04X" % (["A", "B", "C", "X", "Y", "Z", "I", "J"][i],
            self.memory[0x10000 + i]) for i in range(8)))
        print("PC={0:04X} SP={1:04X} O={2:04X}".format(*[self.memory[i] for i in (PC, SP, O)]))
    
    def dump_stack(self):
        if self.memory[SP] == 0x0:
            print("Stack: []")
        else:
            print("Stack: [" + " ".join("%04X" % self.memory[m] for m in range(self.memory[SP], 0x10000)) + "]")


def main(argv):
    plugins = emuplugin.importPlugins()
    parser = argparse.ArgumentParser(description="DCPU-16 emulator", prog=argv[0])
    parser.add_argument("-d", "--debug", action="store_const", const=True, default=False, help="Run emulator in debug mode. This implies '--trace'")
    parser.add_argument("-t", "--trace", action="store_const", const=True, default=False, help="Print dump of registers and stack after every step")
    parser.add_argument("-s", "--speed", action="store_const", const=True, default=False, help="Print speed the emulator is running at in kHz")
    parser.add_argument("object_file", help="File with assembled DCPU binary")
    
    for p in plugins:
        for args in p.arguments:
            parser.add_argument(*args[0], **args[1])
    
    args = parser.parse_args(argv[1:])
    if args.debug:
        args.trace = True
    
    program = []
    with open(args.object_file, "rb") as f:
        word = f.read(2)
        while word:
            program.append(struct.unpack(">H", word)[0])
            word = f.read(2)
    
    plugins_loaded = []
    try:
        for p in plugins:
            p = p(args)
            if p.loaded:
                print("Started plugin: %s" % p.name)
                plugins_loaded.append(p)
        
        dcpu16 = DCPU16(program, plugins_loaded)
        
        dcpu16.run(trace=args.trace, show_speed=args.speed)
    except KeyboardInterrupt:
        pass
    finally:
        for p in plugins_loaded:
            p.shutdown()


def target(*args):
    """Target for PyPy translator."""
    return main, None


if __name__ == "__main__":
    main(sys.argv)
