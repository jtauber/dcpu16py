#!/usr/bin/env python

from __future__ import print_function

import struct
import sys
import argparse


INSTRUCTIONS = [None, "SET", "ADD", "SUB", "MUL", "DIV", "MOD", "SHL", "SHR", "AND", "BOR", "XOR", "IFE", "IFN", "IFG", "IFB"]
IDENTIFERS = ["A", "B", "C", "X", "Y", "Z", "I", "J", "POP", "PEEK", "PUSH", "SP", "PC", "O"]


class Disassembler:

    def __init__(self, program, output=sys.stdout):
        self.program = program
        self.offset = 0
        self.output = output

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

    def next_instruction(self):
        offset = self.offset
        w = self.next_word()

        operands, opcode = divmod(w, 16)
        b, a = divmod(operands, 64)

        if opcode == 0x00:
            if a == 0x01:
                first = "JSR"
            else:
                return
        else:
            first = "%s %s," % (INSTRUCTIONS[opcode], self.format_operand(a))

        asm = "%s %s" % (first, self.format_operand(b))
        binary = " ".join("%04x" % word for word in self.program[offset:self.offset])
        return "%-40s ; %04x: %s" % (asm, offset, binary)

    def run(self):
        while self.offset < len(self.program):
            print(self.next_instruction(), file=self.output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DCPU-16 disassembler")
    parser.add_argument("-o", help="Place the output into FILE instead of stdout", metavar="FILE")
    parser.add_argument("input", help="File with DCPU object code")
    args = parser.parse_args()

    program = []
    if args.input == "-":
        f = sys.stdin
    else:
        f = open(args.input, "rb")
    word = f.read(2)
    while word:
        program.append(struct.unpack(">H", word)[0])
        word = f.read(2)

    output = sys.stdout if args.o is None else open(args.o, "w")
    d = Disassembler(program, output=output)
    d.run()
