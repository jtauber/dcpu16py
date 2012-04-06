#! /usr/bin/env python
"""
pyparsing based grammar for DCPU-16 0x10c assembler
"""

import argparse
import os

import pyparsing as P

# Run with "DEBUG=1 python ./asm_pyparsing.py"
DEBUG = "DEBUG" in os.environ

# otherwise \n is also treated as ignorable whitespace
P.ParserElement.setDefaultWhitespaceChars(' \t')

identifier = P.Word(P.alphas+"_", P.alphanums+"_")
label = P.Combine(P.Literal(":").suppress() + identifier)

comment = P.Literal(";").suppress() + P.restOfLine

register = (P.Word("ABCXYZIJO", max=1, asKeyword=True) | 
            P.Keyword("PC") | 
            P.Keyword("SP"))

stack_op = P.Keyword("PEEK") | P.Keyword("POP") | P.Keyword("PUSH")

hex_literal = P.Combine(P.Literal("0x") + P.Word(P.hexnums))
dec_literal = P.Word(P.nums)

hex_literal.setParseAction(lambda s, l, t: int(t[0], 16))
dec_literal.setParseAction(lambda s, l, t: int(t[0]))

literal = hex_literal | dec_literal | identifier

instruction = P.oneOf("SET ADD SUB MUL DIV MOD SHL SHR AND BOR XOR IFE IFN IFG IFB JSR")
basic_operand = P.Group(register("register") | stack_op("stack_op") | literal("literal"))
indirect_expr = P.Group(literal("literal") + P.Literal("+") + register("register"))

indirection = P.Group(
    (P.Literal("[").suppress() +
     (indirect_expr("expr") | basic_operand("basic")) + 
     P.Literal("]").suppress()))
operand = basic_operand("basic") | indirection("indirect")

statement = (instruction("instruction") + 
             P.Group(operand)("first") + 
             P.Optional(P.Literal(",").suppress() + P.Group(operand)("second"))
            )

line = (P.Optional(label("label")) + 
        P.Optional(statement("statement"), default=None) +
        P.Optional(comment("comment")) + 
        P.lineEnd.suppress())

full_grammar = P.stringStart + P.OneOrMore(P.Group(line)) + P.stringEnd


if DEBUG:
    identifier.setName("identifier").setDebug()
    label.setName("label")
    comment.setName("comment")
    register.setName("register").setDebug()
    stack_op.setName("stack_op").setDebug()
    hex_literal.setName("hex_literal").setDebug()
    dec_literal.setName("dec_literal").setDebug()
    literal.setName("literal").setDebug()
    instruction.setName("instruction").setDebug()
    basic_operand.setName("basic_operand").setDebug()
    indirect_expr.setName("indirect_expr").setDebug()
    indirection.setName("indirection").setDebug()
    operand.setName("operand").setDebug()
    statement.setName("statement").setDebug()
    line.setName("line").setDebug()
    full_grammar.setName("program").setDebug()

IDENTIFIERS = {"A": 0x0, "B": 0x1, "C": 0x2, "X": 0x3, "Y": 0x4, "Z": 0x5,
               "I": 0x6, "J": 0x7, "POP": 0x18, "PEEK": 0x19, "PUSH": 0x1A,
               "SP": 0x1B, "PC": 0x1C}
OPCODES = {"SET": 0x1, "ADD": 0x2, "SUB": 0x3, "MUL": 0x4, "DIV": 0x5,
           "MOD": 0x6, "SHL": 0x7, "SHR": 0x8, "AND": 0x9, "BOR": 0xA,
           "XOR": 0xB, "IFE": 0xC, "IFN": 0xD, "IFG": 0xE, "IFB": 0xF}
        
def process_operand(o):
    if o.basic:
        b = o.basic
        if b.register:
            return IDENTIFIERS[b.register], None
            
        elif b.stack_op:
            return IDENTIFIERS[b.stack_op], None
            
        elif b.literal is not None:
            l = b.literal
            if not isinstance(l, basestring) and l < 0x20:
                return 0x20 | l, None
            assert not l == "", o.asXML()
            return 0x1F, l
            
    elif o.indirect:
        i = o.indirect
        if i.basic:
            ib = i.basic
            if ib.register:
                assert ib.register in "ABCXYZIJ"
                return 0x8 + IDENTIFIERS[ib.register], None
                
            elif ib.literal is not None:
                return 0x1E, ib.literal
            
        elif i.expr:
            ie = i.expr
            assert ie.register in "ABCXYZIJ"
            return 0x10 | IDENTIFIERS[ie.register], ie.literal
    return None, None

def codegen(source):
    
    parsed = full_grammar.parseString(source)
    
    if DEBUG:
        from pprint import pprint
        print(parsed.asXML())
    
    labels = {}
    program = []
    
    for line in parsed:
        if line.label:
            labels[line.label] = len(program)
            
        s = line.statement
        if not s: continue
        
        if s.instruction == "JSR":
            o = 0x00
            a = 0x01
            b, y = process_operand(s.first)
            
        else:
            o = OPCODES[s.instruction]
            a, x = process_operand(s.first)
            b, y = process_operand(s.second)
            
        program.append(((b << 10) + (a << 4) + o))
        if x is not None: program.append(x)
        if y is not None: program.append(y)
        
    # Substitute labels
    for i, c in enumerate(program):
        if isinstance(c, basestring):
            program[i] = labels[c]
    
    # Turn words into bytes
    result = []
    for word in program:
        hi, lo = divmod(word, 0x100)
        result += [hi, lo]
    
    return "".join(chr(c) for c in result)

def main():
    parser = argparse.ArgumentParser(
        description='A simple pyparsing-based DCPU assembly compiler')
    parser.add_argument(
        'source', metavar='IN', type=str,
        help='file path of the file containing the assembly code')
    parser.add_argument(
        'destination', metavar='OUT', type=str, nargs='?',
        help='file path where to store the binary code')
    args = parser.parse_args()
    
    with open(args.source) as fd:
        program = codegen(fd.read())
        
    if not args.destination:
        print program
    else:
        with open(args.destination, "w") as fd:
            fd.write(program)

if __name__ == "__main__":
    main()
