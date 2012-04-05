#!/usr/bin/env python


class Cell:
    
    def __init__(self, value):
        self.value = value


PC, SP, O = 8, 9, 10

class DCPU16:
    
    def __init__(self, memory):
        self.memory = []
        
        for i in range(0x10000):
            if i < len(memory):
                self.memory.append(Cell(memory[i]))
            else:
                self.memory.append(Cell(0x000))
        
        self.registers = (
            Cell(0x0000), # A
            Cell(0x0000), # B
            Cell(0x0000), # C
            Cell(0x0000), # X
            Cell(0x0000), # Y
            Cell(0x0000), # Z
            Cell(0x0000), # I
            Cell(0x0000), # J
            Cell(0x0000), # PC
            Cell(0xFFFF), # SP
            Cell(0x0000), # O
        )
        
        self.skip = False
    
    def SET(self, a, b):
        a.value = b.value
    
    def ADD(self, a, b):
        o, r = divmod(a.value + b.value, 0x10000)
        self.registers[O].value = o
        a.value = r
    
    def SUB(self, a, b):
        o, r = divmod(a.value - b.value, 0x10000)
        self.registers[O].value = 0xFFFF if o == -1 else 0x0000
        a.value = r
    
    def MUL(self, a, b):
        o, r = divmod(a.value + b.value, 0x10000)
        a.value = r
        self.registers[O].value = o % 0x10000
    
    def DIV(self, a, b):
        if b.value == 0x0:
            r = 0x0
            o = 0x0
        else:
            r = a.value / b.value % 0x10000
            o = ((a.value << 16) / b.value) % 0x10000
        a.value = r
        self.registers[O].value = o
    
    def MOD(self, a, b):
        if b.value == 0x0:
            r = 0x0
        else:
            r = a.value % b.value
        a.value = r
    
    def SHL(self, a, b):
        r = a.value << b.value
        o = ((a.value << b.value) >> 16) % 0x10000
        a.value = r
        self.registers[O].value = o
    
    def SHR(self, a, b):
        r = a.value >> b.value
        o = ((a.value << 16) >> b.value) % 0x10000
        a.value = r
        self.registers[O].value = o
    
    def AND(self, a, b):
        a.value = a.value & b.value
    
    def BOR(self, a, b):
        a.value = a.value & b.value
    
    def XOR(self, a, b):
        a.value = a.value ^ b.value
    
    def IFE(self, a, b):
        self.skip = not (a.value == b.value)
    
    def IFN(self, a, b):
        self.skip = not (a.value != b.value)
    
    def IFG(self, a, b):
        self.skip = not (a.value > b.value)
    
    def IFB(self, a, b):
        self.skip = not ((a.value & b.value) != 0)
    
    def JSR(self, a, b):
        self.registers[SP].value -= 1
        pc = self.registers[PC].value
        self.memory[self.registers[SP].value].value = pc
        self.registers[PC].value = b.value
    
    def run(self, debug=False):
        while True:
            pc = self.registers[PC].value
            w = self.memory[pc].value
            self.registers[PC].value += 1
            
            operands, opcode = divmod(w, 16)
            b, a = divmod(operands, 64)
            
            if debug:
                print "%04X: %04X" % (pc, w)
            
            if opcode == 0x00:
                if a == 0x01:
                    op = self.JSR
                else:
                    continue
            else:
                op = [
                    None, self.SET, self.ADD, self.SUB,
                    self.MUL, self.DIV, self.MOD, self.SHL,
                    self.SHR, self.AND, self.BOR, self.XOR, self.IFE, self.IFN, self.IFG, self.IFB
                ][opcode]
                
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
                    self.registers[SP].value += 1
                elif a == 0x19:
                    arg1 = self.memory[self.registers[SP].value]
                elif a == 0x1A:
                    self.registers[SP].value -= 1
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
            
            if b < 0x08:
                arg2 = self.registers[b]
            elif b < 0x10:
                arg2 = self.memory[self.registers[b % 0x08].value]
            elif b < 0x18:
                next_word = self.memory[self.registers[PC].value].value
                self.registers[PC].value += 1
                arg2 = self.memory[next_word + self.registers[b % 0x10].value]
            elif b == 0x18:
                arg2 = self.memory[self.registers[SP].value]
                self.registers[SP].value += 1
            elif b == 0x19:
                arg2 = self.memory[self.registers[SP].value]
            elif b == 0x1A:
                self.registers[SP].value -= 1
                arg2 = self.memory[self.registers[SP].value]
            elif b == 0x1B:
                arg2 = self.registers[SP]
            elif b == 0x1C:
                arg2 = self.registers[PC]
            elif b == 0x1D:
                arg2 = self.registers[O]
            elif b == 0x1E:
                arg2 = self.memory[self.memory[self.registers[PC].value].value]
                self.registers[PC].value += 1
            elif b == 0x1F:
                arg2 = self.memory[self.registers[PC].value]
                self.registers[PC].value += 1
            else:
                arg2 = Cell(b % 0x20)
            
            if self.skip:
                if debug:
                    print "skipping"
                self.skip = False
            else:
                op(arg1, arg2)
                if debug:
                    self.dump_registers()
                    self.dump_stack()
    
    def dump_registers(self):
        print " ".join("%s=%04X" % (["A", "B", "C", "X", "Y", "Z", "I", "J", "PC", "SP", "O"][i],
            self.registers[i].value) for i in range(11))
    
    def dump_stack(self):
        print "[" + " ".join("%04X" % self.memory[m].value for m in range(self.registers[SP].value + 1, 0x10000)) + "]"
    
    def disasm(self):
        while self.registers[PC].value < len(self.memory):
            w = self.memory[self.registers[PC].value].value
            self.registers[PC].value += 1
            
            operands, opcode = divmod(w, 16)
            b, a = divmod(operands, 64)
            
            if opcode == 0x00:
                if a == 0x01:
                    print "JSR",
                else:
                    continue
            else:
                print [
                    None, "SET", "ADD", "SUB", "MUL", "DIV", "MOD", "SHL",
                    "SHR", "AND", "BOR", "XOR", "IFE", "IFN", "IFG", "IFB"
                ][opcode],
                
                if a < 0x08:
                    print "%s," % ["A", "B", "C", "X", "Y", "Z", "I", "J"][a],
                elif a < 0x10:
                    print "[%s]," % ["A", "B", "C", "X", "Y", "Z", "I", "J"][a % 0x08],
                elif a < 0x18:
                    next_word = self.memory[self.registers[PC].value].value
                    self.registers[PC].value += 1
                    print "[0x%02x + %s]," % (next_word, ["A", "B", "C", "X", "Y", "Z", "I", "J"][a % 0x10]),
                elif a < 0x1E:
                    print "%s," % ["POP", "PEEK", "PUSH", "SP", "PC", "O"][a % 0x18],
                elif a == 0x1E:
                    next_word = self.memory[self.registers[PC].value].value
                    self.registers[PC].value += 1
                    print "[0x%02x]," % next_word,
                elif a == 0x1F:
                    next_word = self.memory[self.registers[PC].value].value
                    self.registers[PC].value += 1
                    print "0x%02x," % next_word,
                else:
                    print "0x%02x," % (a % 0x20),
            
            if b < 0x08:
                print "%s" % ["A", "B", "C", "X", "Y", "Z", "I", "J"][b]
            elif b < 0x10:
                print "[%s]" % ["A", "B", "C", "X", "Y", "Z", "I", "J"][b % 0x08]
            elif b < 0x18:
                next_word = self.memory[self.registers[PC].value].value
                self.registers[PC].value += 1
                print "[0x%02x + %s]" % (next_word, ["A", "B", "C", "X", "Y", "Z", "I", "J"][b % 0x10])
            elif b < 0x1E:
                print "%s" % ["POP", "PEEK", "PUSH", "SP", "PC", "O"][b % 0x18]
            elif b == 0x1E:
                next_word = self.memory[self.registers[PC].value].value
                self.registers[PC].value += 1
                print "[0x%02x]" % next_word
            elif b == 0x1F:
                next_word = self.memory[self.registers[PC].value].value
                self.registers[PC].value += 1
                print "0x%02x" % next_word
            else:
                print "0x%02x" % (b % 0x20)


if __name__ == "__main__":
    example = [
        0x7c01, 0x0030, 0x7de1, 0x1000, 0x0020, 0x7803, 0x1000, 0xc00d,
        0x7dc1, 0x001a, 0xa861, 0x7c01, 0x2000, 0x2161, 0x2000, 0x8463,
        0x806d, 0x7dc1, 0x000d, 0x9031, 0x7c10, 0x0018, 0x7dc1, 0x001a,
        0x9037, 0x61c1, 0x7dc1, 0x001a, 0x0000, 0x0000, 0x0000, 0x0000,
    ]
    
    dcpu16 = DCPU16(example)
    dcpu16.disasm()
    
    # run this time
    dcpu16 = DCPU16(example)
    dcpu16.run(debug=True)
