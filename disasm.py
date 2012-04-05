#!/usr/bin/env python


def disasm(program):
    offset = 0
    
    while offset < len(program):
        w = program[offset]
        offset += 1
        
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
                next_word = program[offset]
                offset += 1
                print "[0x%02x + %s]," % (next_word, ["A", "B", "C", "X", "Y", "Z", "I", "J"][a % 0x10]),
            elif a < 0x1E:
                print "%s," % ["POP", "PEEK", "PUSH", "SP", "PC", "O"][a % 0x18],
            elif a == 0x1E:
                next_word = program[offset]
                offset += 1
                print "[0x%02x]," % next_word,
            elif a == 0x1F:
                next_word = program[offset]
                offset += 1
                print "0x%02x," % next_word,
            else:
                print "0x%02x," % (a % 0x20),
            
        if b < 0x08:
            print "%s" % ["A", "B", "C", "X", "Y", "Z", "I", "J"][b]
        elif b < 0x10:
            print "[%s]" % ["A", "B", "C", "X", "Y", "Z", "I", "J"][b % 0x08]
        elif b < 0x18:
            next_word = program[offset]
            offset += 1
            print "[0x%02x + %s]" % (next_word, ["A", "B", "C", "X", "Y", "Z", "I", "J"][b % 0x10])
        elif b < 0x1E:
            print "%s" % ["POP", "PEEK", "PUSH", "SP", "PC", "O"][b % 0x18]
        elif b == 0x1E:
            next_word = program[offset]
            offset += 1
            print "[0x%02x]" % next_word
        elif b == 0x1F:
            next_word = program[offset]
            offset += 1
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
    
    disasm(example)
