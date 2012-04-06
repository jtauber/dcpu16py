#!/usr/bin/env python

import struct
import sys


INSTRUCTIONS = [None, "SET", "ADD", "SUB", "MUL", "DIV", "MOD", "SHL", "SHR", "AND", "BOR", "XOR", "IFE", "IFN", "IFG", "IFB"]
IDENTIFERS = ["A", "B", "C", "X", "Y", "Z", "I", "J", "POP", "PEEK", "PUSH", "SP", "PC", "O"]


class Disassembler:
    
    def __init__(self, program):
        self.program = program
        self.offset = 0
    
    def next_word(self):
        w = self.program[self.offset]
        self.offset += 1
        return w
    
    def format_operand(self, operand):
        if operand < 0x08:
            return "%s" % IDENTIFERS[operand]
        elif operand < 0x10:
            return "[%s]" % IDENTIFERS[operand % 0x08]
        elif operand < 0x18:
            return "[0x%02x + %s]" % (self.next_word(), IDENTIFERS[operand % 0x10])
        elif operand < 0x1E:
            return "%s" % IDENTIFERS[operand % 0x10]
        elif operand == 0x1E:
            return "[0x%02x]" % self.next_word()
        elif operand == 0x1F:
            return "0x%02x" % self.next_word()
        else:
            return "0x%02x" % (operand % 0x20)
    
    def run(self):
        while self.offset < len(self.program):
            offset = self.offset
            w = self.next_word()
            
            operands, opcode = divmod(w, 16)
            b, a = divmod(operands, 64)
            
            if opcode == 0x00:
                if a == 0x01:
                    first = "JSR"
                else:
                    continue
            else:
                first = "%s %s" % (INSTRUCTIONS[opcode], self.format_operand(a))
            
            print("%04x: %s, %s" % (offset, first, self.format_operand(b)))


if __name__ == "__main__":
    if len(sys.argv) == 2:
        program = []
        f = open(sys.argv[1], "rb")
        word = f.read(2)
        while word:
            program.append(struct.unpack(">H", word)[0])
            word = f.read(2)
        
        d = Disassembler(program)
        d.run()
    else:
        print("usage: ./disasm.py <object-file>")
