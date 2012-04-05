#!/usr/bin/env python

import re
import sys

line_regex = re.compile(r"""
    ^
    \s*
    (:(?P<label>\w+))? # label
    \s*
    (
        (
            (?P<basic>SET|ADD|SUB|MUL|DIV|MOD|SHL|SHR|AND|BOR|XOR|IFE|IFN|IFG|IFB) # basic instruction
            \s+
            ( # operand
                (?P<op1_register>A|B|C|X|Y|Z|I|J|POP|PEEK|PUSH|SP|PC|O) # register
                |
                (\[\s*(?P<op1_register_indirect>A|B|C|X|Y|Z|I|J)\s*\]) # register indirect
                |
                (\[\s*(0x(?P<op1_hex_indexed>[0-9A-Fa-f]{1,4}))\s*\+\s*(?P<op1_hex_indexed_index>A|B|C|X|Y|Z|I|J)\s*\]) # hex indexed
                |
                (\[\s*(?P<op1_decimal_indexed>\d+)\s*\+\s*(?P<op1_decimal_indexed_index>A|B|C|X|Y|Z|I|J)\s*\]) # decimal indexed
                |
                (\[\s*(0x(?P<op1_hex_indirect>[0-9A-Fa-f]{1,4}))\s*\]) # hex indirect
                |
                (\[\s*(?P<op1_decimal_indirect>\d+)\s*\]) # decimal indirect
                |
                (0x(?P<op1_hex_literal>[0-9A-Fa-f]{1,4})) # hex literal
                |
                (?P<op1_decimal_literal>\d+) # decimal literal
                |
                (?P<op1_label>\w+) # label+
            )
            \s*
            ,
            \s*
            ( # operand
                (?P<op2_register>A|B|C|X|Y|Z|I|J|POP|PEEK|PUSH|SP|PC|O) # register
                |
                (\[\s*(?P<op2_register_indirect>A|B|C|X|Y|Z|I|J)\s*\]) # register indirect
                |
                (\[\s*(0x(?P<op2_hex_indexed>[0-9A-Fa-f]{1,4}))\s*\+\s*(?P<op2_hex_indexed_index>A|B|C|X|Y|Z|I|J)\s*\]) # hex indexed
                |
                (\[\s*(?P<op2_decimal_indexed>\d+)\s*\+\s*(?P<op2_decimal_indexed_index>A|B|C|X|Y|Z|I|J)\s*\]) # decimal indexed
                |
                (\[\s*(0x(?P<op2_hex_indirect>[0-9A-Fa-f]{1,4}))\s*\]) # hex indirect
                |
                (\[\s*(?P<op2_decimal_indirect>\d+)\s*\]) # decimal indirect
                |
                (0x(?P<op2_hex_literal>[0-9A-Fa-f]{1,4})) # hex literal
                |
                (?P<op2_decimal_literal>\d+) # decimal literal
                |
                (?P<op2_label>\w+) # label+
            )
        )
        |(
            (?P<nonbasic>JSR) # non-basic instruction
            \s+
            ( # operand
                (?P<op3_register>A|B|C|X|Y|Z|I|J|POP|PEEK|PUSH|SP|PC|O) # register
                |
                (\[\s*(?P<op3_register_indirect>A|B|C|X|Y|Z|I|J)\s*\]) # register indirect
                |
                (\[\s*(0x(?P<op3_hex_indexed>[0-9A-Fa-f]{1,4}))\s*\+\s*(?P<op3_hex_indexed_index>A|B|C|X|Y|Z|I|J)\s*\]) # hex indexed
                |
                (\[\s*(?P<op3_decimal_indexed>\d+)\s*\+\s*(?P<op3_decimal_indexed_index>A|B|C|X|Y|Z|I|J)\s*\]) # decimal indexed
                |
                (\[\s*(0x(?P<op3_hex_indirect>[0-9A-Fa-f]{1,4}))\s*\]) # hex indirect
                |
                (\[\s*(?P<op3_decimal_indirect>\d+)\s*\]) # decimal indirect
                |
                (0x(?P<op3_hex_literal>[0-9A-Fa-f]{1,4})) # hex literal
                |
                (?P<op3_decimal_literal>\d+) # decimal literal
                |
                (?P<op3_label>\w+) # label+
            )
        )
    )?
    \s*
    (?P<comment>;.*)? # comment
    $
    """, re.X)


IDENTIFIERS = {"A": 0x0, "B": 0x1, "C": 0x2, "X": 0x3, "Y": 0x4, "Z": 0x5, "I": 0x6, "J": 0x7, "POP": 0x18, "PC": 0x1C}
OPCODES = {"SET": 0x1, "ADD": 0x2, "SUB": 0x3, "MUL": 0x4, "DIV": 0x5, "MOD": 0x6, "SHL": 0x7, "SHR": 0x8, "AND": 0x9, "BOR": 0xA, "XOR": 0xB, "IFE": 0xC, "IFN": 0xD, "IFG": 0xE, "IFB": 0xF}


program = []
labels = {}

if len(sys.argv) == 3:
    input_filename = sys.argv[1]
    output_filename = sys.argv[2]
else:
    print "usage: ./asm.py <input.asm> <output.obj>"
    sys.exit(1)

def report_error(filename, lineno, error):
    print >> sys.stderr, '%s:%i: %s' % (input_filename, lineno, error)

for lineno, line in enumerate(open(input_filename), start=1):
    mo = line_regex.match(line)
    if mo is None:
        report_error(input_filename, lineno, "Syntax error")
        break

    token_dict = mo.groupdict()
    if token_dict is None:
        report_error(input_filename, lineno, "Syntax error")
        break
    
    if token_dict["label"]:
        labels[token_dict["label"]] = len(program)
    
    if token_dict["basic"] is not None:
        o = OPCODES[token_dict["basic"]]
        
        if token_dict["op1_register"] is not None:
            a = IDENTIFIERS[token_dict["op1_register"]]
            x = None
        elif token_dict["op1_register_indirect"] is not None:
            a = 0x08 + IDENTIFIERS[token_dict["op1_register_indirect"]]
            x = None
        elif token_dict["op1_hex_indexed"] is not None:
            a = 0x10 + IDENTIFIERS[token_dict["op1_hex_indexed_index"]]
            x = int(token_dict["op1_hex_indexed"], 16)
        elif token_dict["op1_decimal_indexed"] is not None:
            a = 0x10 + IDENTIFIERS[token_dict["op1_decimal_indexed_index"]]
            x = int(token_dict["op1_decimal_indexed"], 16)
        elif token_dict["op1_hex_indirect"] is not None:
            a = 0x1E
            x = int(token_dict["op1_hex_indirect"], 16)
        elif token_dict["op1_decimal_indirect"] is not None:
            a = 0x1E
            x = int(token_dict["op1_decimal_indirect"])
        elif token_dict["op1_hex_literal"] is not None:
            l = int(token_dict["op1_hex_literal"], 16)
            if l < 0x20:
                a = 0x20 + l
                x = None
            else:
                a = 0x1F
                x = l
        elif token_dict["op1_decimal_literal"] is not None:
            l = int(token_dict["op1_decimal_literal"])
            if l < 0x20:
                a = 0x20 + l
                x = None
            else:
                a = 0x1F
                x = l
        elif token_dict["op1_label"] is not None:
            a = 0x1F
            x = token_dict["op1_label"]
        
        if token_dict["op2_register"] is not None:
            b = IDENTIFIERS[token_dict["op2_register"]]
            y = None
        elif token_dict["op2_register_indirect"] is not None:
            b = 0x08 + IDENTIFIERS[token_dict["op2_register_indirect"]]
            y = None
        elif token_dict["op2_hex_indexed"] is not None:
            b = 0x10 + IDENTIFIERS[token_dict["op2_hex_indexed_index"]]
            y = int(token_dict["op2_hex_indexed"], 16)
        elif token_dict["op2_decimal_indexed"] is not None:
            b = 0x10 + IDENTIFIERS[token_dict["op2_decimal_indexed_index"]]
            y = int(token_dict["op2_decimal_indexed"], 16)
        elif token_dict["op2_hex_indirect"] is not None:
            b = 0x1E
            y = int(token_dict["op2_hex_indirect"], 16)
        elif token_dict["op2_decimal_indirect"] is not None:
            b = 0x1E
            y = int(token_dict["op2_decimal_indirect"])
        elif token_dict["op2_hex_literal"] is not None:
            l = int(token_dict["op2_hex_literal"], 16)
            if l < 0x20:
                b = 0x20 + l
                y = None
            else:
                b = 0x1f
                y = l
        elif token_dict["op2_decimal_literal"] is not None:
            l = int(token_dict["op2_decimal_literal"])
            if l < 0x20:
                b = 0x20 + l
                y = None
            else:
                b = 0x1F
                y = l
        elif token_dict["op2_label"] is not None:
            b = 0x1F
            y = token_dict["op2_label"]
        
        program.append(((b << 10) + (a << 4) + o))
        if x is not None:
            program.append(x)
        if y is not None:
            program.append(y)
    elif token_dict["nonbasic"] is not None:
        o = 0x00
        a = 0x01
        
        y = None
        if token_dict["op3_register"] is not None:
            b = IDENTIFIERS[token_dict["op3_register"]]
        elif token_dict["op3_register_indirect"] is not None:
            b = 0x08 + IDENTIFIERS[token_dict["op3_register_indirect"]]
        elif token_dict["op3_hex_indexed"] is not None:
            b = 0x10 + IDENTIFIERS[token_dict["op3_hex_indexed_index"]]
            y = int(token_dict["op3_hex_indexed"], 16)
        elif token_dict["op3_decimal_indexed"] is not None:
            b = 0x10 + IDENTIFIERS[token_dict["op3_decimal_indexed_index"]]
            y = int(token_dict["op3_decimal_indexed"], 16)
        elif token_dict["op3_hex_indirect"] is not None:
            y = int(token_dict["op3_hex_indirect"], 16)
            b = 0x1E
        elif token_dict["op3_decimal_indirect"] is not None:
            y = int(token_dict["op3_decimal_indirect"])
            b = 0x1E
        elif token_dict["op3_hex_literal"] is not None:
            l = int(token_dict["op3_hex_literal"], 16)
            if l < 0x20:
                b = 0x20 + l
            else:
                b = 0x1F
                y = l
        elif token_dict["op3_decimal_literal"] is not None:
            l = int(token_dict["op3_decimal_literal"])
            if l < 0x20:
                b = 0x20 + l
            else:
                b = 0x1F
                y = l
        elif token_dict["op3_label"] is not None:
            b = 0x1F
            y = token_dict["op3_label"]
        
        program.append(((b << 10) + (a << 4) + o))
        if x is not None:
            program.append(x)
        if y is not None:
            program.append(y)
        
    else: # blank line or comment-only
        pass

with open(output_filename, "wb") as f:
    for word in program:
        if isinstance(word, str):
            word = labels[word]
        hi, lo = divmod(word, 0x100)
        f.write(chr(hi))
        f.write(chr(lo))
