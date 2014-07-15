#! /usr/bin/env python
"""
pyparsing based grammar for DCPU-16 0x10c assembler
"""

try:
    from itertools import izip_longest
except ImportError:
    from itertools import zip_longest as izip_longest

try:
    basestring
except NameError:
    basestring = str

import logging
log = logging.getLogger("dcpu16_asm")
log.setLevel(logging.DEBUG)

import argparse
import os
import struct
import sys

import pyparsing as P
from collections import defaultdict


# Replace the debug actions so that the results go to the debug log rather
# than stdout, so that the output can be usefully piped.
def _defaultStartDebugAction(instring, loc, expr):
    log.debug("Match " + P._ustr(expr) + " at loc " + P._ustr(loc) + "(%d,%d)"
              % (P.lineno(loc, instring), P.col(loc, instring)))


def _defaultSuccessDebugAction(instring, startloc, endloc, expr, toks):
    log.debug("Matched " + P._ustr(expr) + " -> " + str(toks.asList()))


def _defaultExceptionDebugAction(instring, loc, expr, exc):
    log.debug("Exception raised:" + P._ustr(exc))

P._defaultStartDebugAction = _defaultStartDebugAction
P._defaultSuccessDebugAction = _defaultSuccessDebugAction
P._defaultExceptionDebugAction = _defaultExceptionDebugAction


# Run with "DEBUG=1 python ./asm_pyparsing.py"
DEBUG = "DEBUG" in os.environ

WORD_MAX = 0xFFFF

# otherwise \n is also treated as ignorable whitespace
P.ParserElement.setDefaultWhitespaceChars(" \t")

identifier = P.Word(P.alphas + "_", P.alphanums + "_")
label = P.Combine(P.Literal(":").suppress() + identifier)

comment = P.Literal(";").suppress() + P.restOfLine

register = (P.Or(P.CaselessKeyword(x) for x in "ABCIJXYZO")
            | P.oneOf("PC SP", caseless=True))

stack_op = P.oneOf("PEEK POP PUSH", caseless=True)

hex_literal = P.Combine(P.Literal("0x") + P.Word(P.hexnums))
dec_literal = P.Word(P.nums)

numeric_literal = hex_literal | dec_literal
literal = numeric_literal | identifier

opcode = P.oneOf("SET ADD SUB MUL DIV MOD SHL SHR "
                 "AND BOR XOR IFE IFN IFG IFB JSR", caseless=True)

basic_operand = P.Group(register("register")
                        | stack_op("stack_op")
                        | literal("literal"))

indirect_expr = P.Group(literal("literal")
                        + P.Literal("+")
                        + register("register"))

hex_literal.setParseAction(lambda s, l, t: int(t[0], 16))
dec_literal.setParseAction(lambda s, l, t: int(t[0]))
register.addParseAction(P.upcaseTokens)
stack_op.addParseAction(P.upcaseTokens)
opcode.addParseAction(P.upcaseTokens)


def sandwich(brackets, expr):
    l, r = brackets
    return P.Literal(l).suppress() + expr + P.Literal(r).suppress()

indirection_content = indirect_expr("expr") | basic_operand("basic")
indirection = P.Group(sandwich("[]", indirection_content) |
                      sandwich("()", indirection_content))

operand = basic_operand("basic") | indirection("indirect")


def make_words(data):
    return [a << 8 | b for a, b in izip_longest(data[::2], data[1::2], fillvalue=0)]


def wordize_string(s, l, tokens):
    bytes = [ord(c) for c in tokens.string]
    # TODO(pwaller): possibly add syntax for packing string data?
    packed = False
    return make_words(bytes) if packed else bytes

quoted_string = P.quotedString("string").addParseAction(P.removeQuotes).addParseAction(wordize_string)
datum = quoted_string | numeric_literal


def parse_data(string, loc, tokens):
    result = []
    for token in tokens:
        values = datum.parseString(token).asList()
        assert all(v < WORD_MAX for v in values), "Datum exceeds word size"
        result.extend(values)
    return result

# TODO(pwaller): Support for using macro argument values in data statement
datalist = P.commaSeparatedList.copy().setParseAction(parse_data)
data = P.CaselessKeyword("DAT")("opcode") + P.Group(datalist)("data")

line = P.Forward()

macro_definition_args = P.Group(P.delimitedList(P.Optional(identifier("arg"))))("args")

macro_definition = P.Group(
    P.CaselessKeyword("#macro").suppress()
    + identifier("name")
    + sandwich("()", macro_definition_args)
    + sandwich("{}", P.Group(P.OneOrMore(line))("lines"))
)("macro_definition")

macro_argument = operand | datum

macro_call_args = P.Group(P.delimitedList(P.Group(macro_argument)("arg")))("args")

macro_call = P.Group(
    identifier("name") + sandwich("()", macro_call_args)
)("macro_call")

instruction = (
    opcode("opcode")
    + P.Group(operand)("first")
    + P.Optional(P.Literal(",").suppress() + P.Group(operand)("second"))
)

statement = P.Group(
    instruction
    | data
    | macro_definition
    | macro_call
)

line << P.Group(
    P.Optional(label("label"))
    + P.Optional(statement("statement"), default=None)
    + P.Optional(comment("comment"))
    + P.lineEnd.suppress()
)("line")

full_grammar = (
    P.stringStart
    + P.ZeroOrMore(line)
    + (P.stringEnd | P.Literal("#stop").suppress())
)("program")


if DEBUG:
    # Turn setdebug on for all parse elements
    for name, var in locals().copy().items():
        if isinstance(var, P.ParserElement):
            var.setName(name).setDebug()

    def debug_line(string, location, tokens):
        """
        Show the current line number and content being parsed
        """
        lineno = string[:location].count("\n")
        remaining = string[location:]
        line_end = remaining.index("\n") if "\n" in remaining else None
        log.debug("====")
        log.debug("  Parse line {0}".format(lineno))
        log.debug("  '{0}'".format(remaining[:line_end]))
        log.debug("====")
    line.setDebugActions(debug_line, None, None)

IDENTIFIERS = {"A": 0x0, "B": 0x1, "C": 0x2, "X": 0x3, "Y": 0x4, "Z": 0x5,
               "I": 0x6, "J": 0x7,
               "POP": 0x18, "PEEK": 0x19, "PUSH": 0x1A,
               "SP": 0x1B, "PC": 0x1C,
               "O": 0x1D}
OPCODES = {"SET": 0x1, "ADD": 0x2, "SUB": 0x3, "MUL": 0x4, "DIV": 0x5,
           "MOD": 0x6, "SHL": 0x7, "SHR": 0x8, "AND": 0x9, "BOR": 0xA,
           "XOR": 0xB, "IFE": 0xC, "IFN": 0xD, "IFG": 0xE, "IFB": 0xF}


def process_operand(o, lvalue=False):
    """
    Returns (a, x) where a is a value which identifies the nature of the value
    and x is either None or a word to be inserted directly into the output stream
    (e.g. a literal value >= 0x20)
    """
    # TODO(pwaller): Reject invalid lvalues

    def invalid_op(reason):
        # TODO(pwaller): Need to indicate origin of error
        return RuntimeError("Invalid operand, {0}: {1}"
                            .format(reason, o.asXML()))

    def check_indirect_register(register):
        if register not in "ABCXYZIJ":
            raise invalid_op("only registers A-J can be used for indirection")

    if o.basic:
        # Literals, stack ops, registers
        b = o.basic
        if b.register:
            return IDENTIFIERS[b.register], None

        elif b.stack_op:
            return IDENTIFIERS[b.stack_op], None

        elif b.literal is not None:
            l = b.literal
            if not isinstance(l, basestring) and l < 0x20:
                return 0x20 | l, None
            if l == "":
                raise invalid_op("this is a bug")
            if isinstance(l, int) and not 0 <= l <= WORD_MAX:
                raise invalid_op("literal exceeds word size")
            return 0x1F, l

    elif o.indirect:
        i = o.indirect
        if i.basic:
            # [register], [literal]
            ib = i.basic
            if ib.register:
                check_indirect_register(ib.register)
                return 0x8 + IDENTIFIERS[ib.register], None

            elif ib.stack_op:
                raise invalid_op("don't use PUSH/POP/PEEK with indirection")

            elif ib.literal is not None:
                return 0x1E, ib.literal

        elif i.expr:
            # [register+literal]
            ie = i.expr
            check_indirect_register(ie.register)
            return 0x10 | IDENTIFIERS[ie.register], ie.literal

    raise invalid_op("this is a bug")


def codegen(source, input_filename="<unknown>"):

    try:
        parsed = full_grammar.parseString(source)
    except P.ParseException as exc:
        log.fatal("Parse error:")
        log.fatal("  {0}:{1}:{2} HERE {3}"
                  .format(input_filename, exc.lineno, exc.col,
                          exc.markInputline()))
        return None

    log.debug("=====")
    log.debug("  Successful parse, XML syntax interpretation:")
    log.debug("=====")
    log.debug(parsed.asXML())

    labels = {}
    macros = {}
    program = []
    # Number of times a given macro has been called so that we can generate
    # unique labels
    n_macro_calls = defaultdict(int)

    def process_macro_definition(statement):
        log.debug("Macro definition: {0}".format(statement.asXML()))
        macros[statement.name] = statement

    def process_macro_call(offset, statement, context=""):
        log.debug("--------------")
        log.debug("Macro call: {0}".format(statement.asXML()))
        log.debug("--------------")

        macroname = statement.name
        macro = macros.get(macroname, None)
        n_macro_calls[macroname] += 1
        context = context + macroname + str(n_macro_calls[macroname])

        if not macro:
            raise RuntimeError("Call to undefined macro: {0}".format(macroname))

        assert len(macro.args) == len(statement.args), (
            "Wrong number of arguments to macro call {0!r}".format(macroname))

        # TODO(pwaller): Check for collisions between argument name and code
        #                label
        args = {}

        log.debug("Populated args:")
        for name, arg in zip(macro.args, statement.args):
            args[name] = arg
            log.debug("  - {0}: {1}".format(name, arg))

        lines = []

        for l in macro.lines:
            new_line = l.copy()
            s = l.statement
            if s:
                new_statement = s.copy()
                new_line["statement"] = new_statement
            #if l.label: new_line["label"] = context + l.label

            # Replace literals whose names are macro arguments
            # also, substitute labels with (context, label).
            # Resolution of a label happens later by first searching for a label
            # called `context + label`, and if it doesn't exist `label` is used.
            if s and s.first and s.first.basic and s.first.basic.literal:
                if s.first.basic.literal in args:
                    new_statement["first"] = args[s.first.basic.literal]
                elif isinstance(s.first.basic.literal, basestring):
                    new_basic = s.first.basic.copy()
                    new_basic["literal"] = context, s.first.basic.literal
                    new_op = new_statement.first.copy()
                    new_op["basic"] = new_basic
                    new_statement["first"] = new_op

            if s and s.second and s.second.basic and s.second.basic.literal:
                if s.second.basic.literal in args:
                    new_statement["second"] = args[s.second.basic.literal]
                elif isinstance(s.second.basic.literal, basestring):
                    new_basic = s.second.basic.copy()
                    new_basic["literal"] = context, s.second.basic.literal
                    new_op = new_statement.second.copy()
                    new_op["basic"] = new_basic
                    new_statement["second"] = new_op

            # Replace macro call arguments
            if s and s.macro_call:
                new_macro_call = s.macro_call.copy()
                new_statement["macro_call"] = new_macro_call
                new_macro_call_args = s.macro_call.args.copy()
                new_statement.macro_call["args"] = new_macro_call_args
                for i, arg in enumerate(s.macro_call.args):
                    if arg.basic.literal not in args:
                        continue
                    new_macro_call_args[i] = args[arg.basic.literal]

            lines.append(new_line)

        log.debug("Populated macro: {0}"
                  .format("\n".join(l.dump() for l in lines)))

        # Do code generation
        code = []
        for l in lines:
            a = generate(offset + len(code), l, context)
            log.debug("Codegen for statement: {0}".format(l.asXML()))
            log.debug("  Code: {0}".format(a))
            code.extend(a)
        return code

    def generate(offset, line, context=""):
        log.debug("Interpreting element {0}: {1}".format(i, line))
        if line.label:
            label = context + line.label
            if label in labels:
                # TODO(pwaller): Line indications
                msg = "Duplicate label definition! {0}".format(label)
                log.fatal(msg)
                raise RuntimeError(msg)
            labels[label] = offset

        s = line.statement
        if not s:
            return []

        if s.macro_definition:
            process_macro_definition(s.macro_definition)
            return []
        elif s.macro_call:
            return process_macro_call(offset, s.macro_call, context)

        log.debug("Generating for {0}".format(s.asXML(formatted=False)))
        if s.opcode == "DAT":
            return s.data

        if s.opcode == "JSR":
            o = 0x00
            a, x = 0x01, None
            b, y = process_operand(s.first)

        else:
            o = OPCODES[s.opcode]
            a, x = process_operand(s.first, lvalue=True)
            b, y = process_operand(s.second)

        code = []
        code.append(((b << 10) + (a << 4) + o))
        if x is not None:
            code.append(x)
        if y is not None:
            code.append(y)
        return code

    for i, line in enumerate(parsed):
        program.extend(generate(len(program), line))

    log.debug("Labels: {0}".format(labels))

    log.debug("program: {0}".format(program))

    # Substitute labels
    for i, c in enumerate(program):
        if isinstance(c, basestring):
            if c not in labels:
                raise RuntimeError("Undefined label used: {0}".format(c))
            program[i] = labels[c]
        elif isinstance(c, tuple):
            context, label = c
            if context + label in labels:
                label = context + label
            if label not in labels:
                raise RuntimeError("Undefined label used: {0}".format(c))
            program[i] = labels[label]

    # Turn words into bytes
    result = bytes()
    for word in program:
        result += struct.pack(">H", word)
    return result


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

    if not log.handlers:
        from sys import stderr
        handler = logging.StreamHandler(stderr)
        log.addHandler(handler)
        if not DEBUG:
            handler.setLevel(logging.INFO)

    if args.source == "-":
        program = codegen(sys.stdin.read(), "<stdin>")
    else:
        with open(args.source) as fd:
            program = codegen(fd.read(), args.source)

    if program is None:
        log.fatal("No program produced.")
        if not DEBUG:
            log.fatal("Run with DEBUG=1 ./asm_pyparsing.py "
                      "for more information.")
        return 1

    if not args.destination:
        if os.isatty(sys.stdout.fileno()):
            log.fatal("stdout is a tty, not writing binary. "
                      "Specify destination file or pipe output somewhere")
        else:
            sys.stdout.write(program)
    else:
        with open(args.destination, "wb") as fd:
            fd.write(program)
    log.info("Program written to {0} ({1} bytes, hash={2})"
             .format(args.destination, len(program),
                     hex(abs(hash(program)))))

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
