#!/usr/bin/env python

from __future__ import print_function

import struct
import re
import sys
import argparse
import os
import codecs


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
        (\[\s*(?P<""" + prefix + """label_indirect>\w+)\s*\]) # label indirect
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


IDENTIFIERS = {
    "A": 0x0,
    "B": 0x1,
    "C": 0x2,
    "X": 0x3,
    "Y": 0x4,
    "Z": 0x5,
    "I": 0x6,
    "J": 0x7,
    "POP": 0x18,
    "PEEK": 0x19,
    "PUSH": 0x1a,
    "SP": 0x1b,
    "PC": 0x1C,
    "O": 0x1D
}

OPCODES = {
    "SET": 0x1,
    "ADD": 0x2,
    "SUB": 0x3,
    "MUL": 0x4,
    "DIV": 0x5,
    "MOD": 0x6,
    "SHL": 0x7,
    "SHR": 0x8,
    "AND": 0x9,
    "BOR": 0xA,
    "XOR": 0xB,
    "IFE": 0xC,
    "IFN": 0xD,
    "IFG": 0xE,
    "IFB": 0xF
}


def clamped_value(l):
    return (0x20 + l, None) if l < 0x20 else (0x1F, l)


ADDR_MAP = {
    "register": lambda t, v: (IDENTIFIERS[t.upper()], None),
    "register_indirect": lambda t, v: (0x08 + IDENTIFIERS[t.upper()], None),
    "hex_indexed_index": lambda t, v: (0x10 + IDENTIFIERS[t.upper()], int(v, 16)),
    "decimal_indexed_index": lambda t, v: (0x10 + IDENTIFIERS[t.upper()], int(v, 16)),
    "label_indexed_index": lambda t, v: (0x10 + IDENTIFIERS[t.upper()], v),
    "hex_indirect": lambda t, v: (0x1E, int(t, 16)),
    "decimal_indirect": lambda t, v: (0x1E, int(t)),
    "hex_literal": lambda t, v: clamped_value(int(t, 16)),
    "decimal_literal": lambda t, v: clamped_value(int(t)),
    "label_indirect": lambda t, v: (0x1E, t),
    "label": lambda t, v: (0x1F, t),
}


def handle(token_dict, prefix):
    token = [t for t in token_dict.keys() if t.startswith(prefix) and token_dict[t] is not None][0]
    suffix = token[len(prefix):]
    v = token_dict[token[:token.rfind("_index")]] if token.endswith("_index") else None
    return ADDR_MAP[suffix](token_dict[token], v)


def report_error(filename, lineno, error):
    print("%s:%i: %s" % (filename, lineno, error), file=sys.stderr)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="DCPU-16 assembler")
    parser.add_argument("-o", default="a.obj", help="Place the output into FILE", metavar="FILE")
    parser.add_argument("input", help="File with DCPU assembly code")
    args = parser.parse_args()

    program = []
    labels = {}

    for lineno, line in enumerate(open(args.input), start=1):
        if lineno == 1:
            line = line.lstrip(codecs.BOM_UTF8)

        mo = line_regex.match(line)
        if mo is None:
            report_error(args.input, lineno, "Syntax error: '%s'" % line.strip())
            break

        token_dict = mo.groupdict()
        if token_dict is None:
            report_error(args.input, lineno, "Syntax error: '%s'" % line.strip())
            break

        if token_dict["label"] is not None:
            labels[token_dict["label"]] = len(program)

        o = x = y = None
        if token_dict["basic"] is not None:
            o = OPCODES[token_dict["basic"].upper()]
            a, x = handle(token_dict, "op1_")
            b, y = handle(token_dict, "op2_")
        elif token_dict["nonbasic"] is not None:
            o, a = 0x00, 0x01
            b, y = handle(token_dict, "op3_")
        elif token_dict["data"] is not None:
            for datum in re.findall("""("[^"]*"|0x[0-9A-Fa-f]{1,4}|\d+)""", token_dict["data"]):
                if datum.startswith("\""):
                    program.extend(ord(ch) for ch in datum[1:-1])
                elif datum.startswith("0x"):
                    program.append(int(datum[2:], 16))
                else:
                    program.append(int(datum))

        if o is not None:
            program.append(((b << 10) + (a << 4) + o))
        if x is not None:
            program.append(x)
        if y is not None:
            program.append(y)

    try:
        with open(args.o, "wb") as f:
            for word in program:
                if isinstance(word, str):
                    word = labels[word]
                f.write(struct.pack(">H", word))
    except KeyError:
        os.remove(args.o)
