#!/usr/bin/env python

from __future__ import print_function

import struct
import re
import sys


def disjunction(*lst):
    "make a uppercase/lowercase disjunction out of a list of strings"
    return "|".join([item.upper() for item in lst] + [item.lower() for item in lst])


BASIC_INSTRUCTIONS = disjunction("SET", "ADD", "SUB", "MUL", "DIV", "MOD", "SHL", "SHR", "AND", "BOR", "XOR", "IFE", "IFN", "IFG", "IFB")
GENERAL_REGISTERS = disjunction("A", "B", "C", "X", "Y", "Z", "I", "J")
ALL_REGISTERS = disjunction("A", "B", "C", "X", "Y", "Z", "I", "J", "POP", "PEEK", "PUSH", "SP", "PC", "O")


def operand_re(prefix):
    return """
    ( # operand
        (?P<""" + prefix + """register>""" + ALL_REGISTERS + """) # register
        |
        (\[\s*(?P<""" + prefix + """register_indirect>""" + GENERAL_REGISTERS + """)\s*\]) # register indirect
        |
        (\[\s*(0x(?P<""" + prefix + """hex_indexed>[0-9A-Fa-f]{1,4}))\s*\+\s*(?P<""" + prefix + """hex_indexed_index>""" + GENERAL_REGISTERS + """)\s*\]) # hex indexed
        |
        (\[\s*(?P<""" + prefix + """decimal_indexed>\d+)\s*\+\s*(?P<""" + prefix + """decimal_indexed_index>""" + GENERAL_REGISTERS + """)\s*\]) # decimal indexed
        |
        (\[\s*(?P<""" + prefix + """label_indexed>\w+)\s*\+\s*(?P<""" + prefix + """label_indexed_index>""" + GENERAL_REGISTERS + """)\s*\]) # label indexed
        |
        (\[\s*(0x(?P<""" + prefix + """hex_indirect>[0-9A-Fa-f]{1,4}))\s*\]) # hex indirect
        |
        (\[\s*(?P<""" + prefix + """decimal_indirect>\d+)\s*\]) # decimal indirect
        |
        (0x(?P<""" + prefix + """hex_literal>[0-9A-Fa-f]{1,4})) # hex literal
        |
        (?P<""" + prefix + """decimal_literal>\d+) # decimal literal
        |
        (?P<""" + prefix + """label>\w+) # label+
    )
    """

line_regex = re.compile(r"""^\s*
    (:(?P<label>\w+))? # label
    \s*
    (
        (
            (?P<basic>""" + BASIC_INSTRUCTIONS + """) # basic instruction
            \s+""" + operand_re("op1_") + """\s*,\s*""" + operand_re("op2_") + """
        )
        |(
            (?P<nonbasic>JSR|jsr) # non-basic instruction
            \s+""" + operand_re("op3_") + """
        )
        |(
            (DAT|dat) # data
            \s+(?P<data>("[^"]*"|0x[0-9A-Fa-f]{1,4}|\d+)(,\s*("[^"]*"|0x[0-9A-Fa-f]{1,4}|\d+))*)
        )
    )?
    \s*
    (?P<comment>;.*)? # comment
    $""", re.X)


IDENTIFIERS = {"A": 0x0, "B": 0x1, "C": 0x2, "X": 0x3, "Y": 0x4, "Z": 0x5, "I": 0x6, "J": 0x7, "POP": 0x18, "PC": 0x1C}
OPCODES = {"SET": 0x1, "ADD": 0x2, "SUB": 0x3, "MUL": 0x4, "DIV": 0x5, "MOD": 0x6, "SHL": 0x7, "SHR": 0x8, "AND": 0x9, "BOR": 0xA, "XOR": 0xB, "IFE": 0xC, "IFN": 0xD, "IFG": 0xE, "IFB": 0xF}


def handle(token_dict, prefix):
    x = None
    if token_dict[prefix + "register"] is not None:
        a = IDENTIFIERS[token_dict[prefix + "register"].upper()]
    elif token_dict[prefix + "register_indirect"] is not None:
        a = 0x08 + IDENTIFIERS[token_dict[prefix + "register_indirect"].upper()]
    elif token_dict[prefix + "hex_indexed"] is not None:
        a = 0x10 + IDENTIFIERS[token_dict[prefix + "hex_indexed_index"].upper()]
        x = int(token_dict[prefix + "hex_indexed"], 16)
    elif token_dict[prefix + "decimal_indexed"] is not None:
        a = 0x10 + IDENTIFIERS[token_dict[prefix + "decimal_indexed_index"].upper()]
        x = int(token_dict[prefix + "decimal_indexed"], 16)
    elif token_dict[prefix + "label_indexed"] is not None:
        a = 0x10 + IDENTIFIERS[token_dict[prefix + "label_indexed_index"].upper()]
        x = token_dict[prefix + "label_indexed"]
    elif token_dict[prefix + "hex_indirect"] is not None:
        a = 0x1E
        x = int(token_dict[prefix + "hex_indirect"], 16)
    elif token_dict[prefix + "decimal_indirect"] is not None:
        a = 0x1E
        x = int(token_dict[prefix + "decimal_indirect"])
    elif token_dict[prefix + "hex_literal"] is not None:
        l = int(token_dict[prefix + "hex_literal"], 16)
        if l < 0x20:
            a = 0x20 + l
        else:
            a = 0x1F
            x = l
    elif token_dict[prefix + "decimal_literal"] is not None:
        l = int(token_dict[prefix + "decimal_literal"])
        if l < 0x20:
            a = 0x20 + l
        else:
            a = 0x1F
            x = l
    elif token_dict[prefix + "label"] is not None:
        a = 0x1F
        x = token_dict[prefix + "label"]
    
    return a, x


program = []
labels = {}


if len(sys.argv) == 3:
    input_filename = sys.argv[1]
    output_filename = sys.argv[2]
else:
    print("usage: ./asm.py <input.asm> <output.obj>")
    sys.exit(1)


def report_error(filename, lineno, error):
    print("%s:%i: %s" % (input_filename, lineno, error), file=sys.stderr)


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
        o = OPCODES[token_dict["basic"].upper()]
        a, x = handle(token_dict, "op1_")
        b, y = handle(token_dict, "op2_")
    elif token_dict["nonbasic"] is not None:
        o, a, x = 0x00, 0x01, None
        b, y = handle(token_dict, "op3_")
    elif token_dict["data"] is not None:
        o = None
        for datum in re.findall("""("[^"]*"|0x[0-9A-Fa-f]{1,4}|\d+)""", token_dict["data"]):
            if datum.startswith("\""):
                program.extend(ord(ch) for ch in datum[1:-1])
            elif datum.startswith("0x"):
                program.append(int(datum[2:], 16))
            else:
                program.append(int(datum))
    else: # blank line or comment-only
        o = x = y = None
    
    if o is not None:
        program.append(((b << 10) + (a << 4) + o))
    if x is not None:
        program.append(x)
    if y is not None:
        program.append(y)


with open(output_filename, "wb") as f:
    for word in program:
        if isinstance(word, str):
            word = labels[word]
        f.write(struct.pack(">H", word))
