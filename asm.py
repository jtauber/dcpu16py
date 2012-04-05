#!/usr/bin/env python

import re


example = """
; Try some basic stuff
                      SET A, 0x30              ; 7c01 0030
                      SET [0x1000], 0x20       ; 7de1 1000 0020
                      SUB A, [0x1000]          ; 7803 1000
                      IFN A, 0x10              ; c00d 
                         SET PC, crash         ; 7dc1 001a [*]
                      
        ; Do a loopy thing
                      SET I, 10                ; a861
                      SET A, 0x2000            ; 7c01 2000
        :loop         SET [0x2000+I], [A]      ; 2161 2000
                      SUB I, 1                 ; 8463
                      IFN I, 0                 ; 806d
                         SET PC, loop          ; 7dc1 000d [*]
        
        ; Call a subroutine
                      SET X, 0x4               ; 9031
                      JSR testsub              ; 7c10 0018 [*]
                      SET PC, crash            ; 7dc1 001a [*]
        
        :testsub      SHL X, 4                 ; 9037
                      SET PC, POP              ; 61c1
                        
        ; Hang forever. X should now be 0x40 if everything went right.
        :crash        SET PC, crash            ; 7dc1 001a [*]
        
        ; [*]: Note that these can be one word shorter and one cycle faster by using the short form (0x00-0x1f) of literals,
        ;      but my assembler doesn't support short form labels yet.     
"""


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

for line in example.split("\n"):
    token_dict = line_regex.match(line).groupdict()
    if token_dict is None:
        print "syntax error: %s" % line
        break
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
            x = 0xFFFF
        
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
            y = 0xFFFF
        
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
            y = 0xFFFF
        
        program.append(((b << 10) + (a << 4) + o))
        if x is not None:
            program.append(x)
        if y is not None:
            program.append(y)
        
    else: # blank line or comment-only
        pass

for word in program:
    print "%04x" % word