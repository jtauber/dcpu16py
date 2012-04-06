#!/usr/bin/env python


import sys
import inspect

class Cell:
    """
    a cell enables us to pass around a reference to a register or memory location rather than the value
    """
    def __init__(self, value=0):
        self.value = value


# offsets into DCPU16.registers
PC, SP, O = 8, 9, 10

def opcode(code):
    """A decorator for opcodes"""
    def decorator(func):
        setattr(func, "_is_opcode", True)
        setattr(func, "_opcode", code)
        return func
    
    return decorator


class DCPU16:
    
    def __init__(self, memory):
        self.memory = [Cell(memory[i]) if i < len(memory) else Cell() for i in range(0x10000)]
        self.registers = tuple(Cell() for _ in range(11))
        self.skip = False

        self.opcodes = {}
        for name, value in inspect.getmembers(self):
            if inspect.ismethod(value) and getattr(value, "_is_opcode", False):
                self.opcodes[getattr(value, "_opcode")] = value 
    
    @opcode(0x01)
    def SET(self, a, b):
        a.value = b.value
    
    @opcode(0x02)
    def ADD(self, a, b):
        o, r = divmod(a.value + b.value, 0x10000)
        self.registers[O].value = o
        a.value = r
    
    @opcode(0x03)
    def SUB(self, a, b):
        o, r = divmod(a.value - b.value, 0x10000)
        self.registers[O].value = 0xFFFF if o == -1 else 0x0000
        a.value = r
    
    @opcode(0x04)
    def MUL(self, a, b):
        o, r = divmod(a.value * b.value, 0x10000)
        a.value = r
        self.registers[O].value = o % 0x10000
    
    @opcode(0x05)
    def DIV(self, a, b):
        if b.value == 0x0:
            r = 0x0
            o = 0x0
        else:
            r = a.value / b.value % 0x10000
            o = ((a.value << 16) / b.value) % 0x10000
        a.value = r
        self.registers[O].value = o
    
    @opcode(0x06)
    def MOD(self, a, b):
        if b.value == 0x0:
            r = 0x0
        else:
            r = a.value % b.value
        a.value = r
    
    @opcode(0x07)
    def SHL(self, a, b):
        r = a.value << b.value
        o = ((a.value << b.value) >> 16) % 0x10000
        a.value = r
        self.registers[O].value = o
    
    @opcode(0x08)
    def SHR(self, a, b):
        r = a.value >> b.value
        o = ((a.value << 16) >> b.value) % 0x10000
        a.value = r
        self.registers[O].value = o
    
    @opcode(0x09)
    def AND(self, a, b):
        a.value = a.value & b.value
    
    @opcode(0x0a)
    def BOR(self, a, b):
        a.value = a.value | b.value
    
    @opcode(0x0b)
    def XOR(self, a, b):
        a.value = a.value ^ b.value
    
    @opcode(0x0c)
    def IFE(self, a, b):
        self.skip = not (a.value == b.value)
    
    @opcode(0x0d)
    def IFN(self, a, b):
        self.skip = not (a.value != b.value)
    
    @opcode(0x0e)
    def IFG(self, a, b):
        self.skip = not (a.value > b.value)
    
    @opcode(0x0f)
    def IFB(self, a, b):
        self.skip = not ((a.value & b.value) != 0)
    
    @opcode(0x010)
    def JSR(self, a, b):
        self.registers[SP].value = (self.registers[SP].value - 1) % 0x10000
        pc = self.registers[PC].value
        self.memory[self.registers[SP].value].value = pc
        self.registers[PC].value = b.value
    
    def get_operand(self, a):
        if a < 0x08:
            arg1 = self.registers[a]
        elif a < 0x10:
            arg1 = self.memory[self.registers[a % 0x08].value]
        elif a < 0x18:
            next_word = self.memory[self.registers[PC].value].value
            self.registers[PC].value += 1
            arg1 = self.memory[next_word + self.registers[a % 0x10].value]
        elif a == 0x18:
            arg1 = self.memory[self.registers[SP].value]
            self.registers[SP].value = (self.registers[SP].value + 1) % 0x10000
        elif a == 0x19:
            arg1 = self.memory[self.registers[SP].value]
        elif a == 0x1A:
            self.registers[SP].value = (self.registers[SP].value - 1) % 0x10000
            arg1 = self.memory[self.registers[SP].value]
        elif a == 0x1B:
            arg1 = self.registers[SP]
        elif a == 0x1C:
            arg1 = self.registers[PC]
        elif a == 0x1D:
            arg1 = self.registers[O]
        elif a == 0x1E:
            arg1 = self.memory[self.memory[self.registers[PC].value].value]
            self.registers[PC].value += 1
        elif a == 0x1F:
            arg1 = self.memory[self.registers[PC].value]
            self.registers[PC].value += 1
        else:
            arg1 = Cell(a % 0x20)
        
        return arg1
    
    def run(self, debug=False):
        while True:
            pc = self.registers[PC].value
            w = self.memory[pc].value
            self.registers[PC].value += 1
            
            operands, opcode = divmod(w, 16)
            b, a = divmod(operands, 64)
            
            if debug:
                print("%04X: %04X" % (pc, w))
            
            if opcode == 0x00:
                arg1 = None
                opcode = (a << 4) + 0x0
            else:
                arg1 = self.get_operand(a)

            op = self.opcodes[opcode]
            arg2 = self.get_operand(b)
            
            if self.skip:
                if debug:
                    print("skipping")
                self.skip = False
            else:
                op(arg1, arg2)
                if debug:
                    self.dump_registers()
                    self.dump_stack()
    
    def dump_registers(self):
        print(" ".join("%s=%04X" % (["A", "B", "C", "X", "Y", "Z", "I", "J", "PC", "SP", "O"][i],
            self.registers[i].value) for i in range(11)))
    
    def dump_stack(self):
        if self.registers[SP].value == 0x0:
            print("[]")
        else:
            print("[" + " ".join("%04X" % self.memory[m].value for m in range(self.registers[SP].value, 0x10000)) + "]")


if __name__ == "__main__":
    if len(sys.argv) == 2:
        program = []
        f = open(sys.argv[1], "rb")
        while True:
            hi = f.read(1)
            if not hi:
                break
            lo = f.read(1)
            program.append((ord(hi) << 8) + ord(lo))
        
        dcpu16 = DCPU16(program)
        dcpu16.run(debug=True)
    else:
        print("usage: ./dcpu16.py <object-file>")
