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


for line in example.split("\n"):
    print {k: v for k, v in line_regex.match(line).groupdict().items() if v is not None}
