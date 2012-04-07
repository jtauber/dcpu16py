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

import logging; log = logging.getLogger("dcpu16_asm")
log.setLevel(logging.DEBUG)

import argparse
import os
import struct
import sys

import pyparsing as P


# Run with "DEBUG=1 python ./asm_pyparsing.py"
DEBUG = "DEBUG" in os.environ

WORD_MAX = 0xFFFF

# otherwise \n is also treated as ignorable whitespace
P.ParserElement.setDefaultWhitespaceChars(" \t")

identifier = P.Word(P.alphas+"_", P.alphanums+"_")
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
    return [a << 8 | b for a, b in izip_longest(data[::2], data[1::2],
                                                  fillvalue=0)]
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

#commasepitem = P.Combine(P.OneOrMore(Word(_noncomma) + Optional( Word(" \t") +  ~Literal(",") + ~LineEnd() ) ) ).streamline()
macro_definition_args = P.Group(P.delimitedList(P.Optional(identifier("arg"))))("args")

macro_definition = P.Group(
    P.CaselessKeyword("#macro").suppress()
    + identifier("name")
    + sandwich("()", macro_definition_args)
    + sandwich("{}", P.Group(P.OneOrMore(line))("statements"))
)("macro_definition")

macro_argument = operand | datum

macro_call_args = P.Group(P.delimitedList(P.Optional(macro_argument)))("args")

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

line << (
    P.Optional(label("label"))
    + P.Optional(statement("statement"), default=None)
    + P.Optional(comment("comment"))
    + P.lineEnd.suppress()
)("line")

full_grammar = (P.stringStart + P.OneOrMore(P.Group(line)) + P.stringEnd)("program")


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
               "I": 0x6, "J": 0x7, "POP": 0x18, "PEEK": 0x19, "PUSH": 0x1A,
               "SP": 0x1B, "PC": 0x1C}
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
            if l == "": raise invalid_op("this is a bug")
            if isinstance(l, (int, long)) and not 0 <= l <= WORD_MAX:
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
    
    def process_macro_definition(statement):
        log.debug("Macro definition: {0}".format(statement.asXML()))
        macros[statement.name] = statement
        
    def process_macro_call(statement):
        log.debug("Macro call: {0}".format(statement.asXML()))
        macroname = statement.name
        macro = macros.get(macroname, None)
        if not macro:
            raise RuntimeError("Call to undefined macro: {0}".format(macroname))
        
        log.debug("Macrodef args: {0!r}".format(macro.args))
        log.debug("Macrouse args: {0!r}".format(statement.args))
        
        assert len(macro.args) == len(statement.args), (
            "Wrong number of arguments to macro call {0!r}".format(macroname))
        
        # TODO(pwaller): Check for collisions between argument name and code 
        # label
        args = dict(zip(macro.args, statement.args))
        #for argdef, argvalue in zip(macro.args, statement.args):
            #log.debug("argdef = {0} argvalue = {1}".format(argdef, argvalue))
            #args[argdef] = argvalue
        
        log.debug("Populated args: {0}".format(args))
         
        statements = []
        
        # Replace label literals which are macro arguments with their values
        for s in macro.statements:
            if not s: continue
            statement = s.copy()
            if s and s.first and s.first.basic and s.first.basic.literal:
                if s.first.basic.literal in args:
                    statement["first"] = args[s.first.basic.literal]
            if s and s.second and s.second.basic and s.second.basic.literal:
                if s.second.basic.literal in args:
                    n = s.second.basic.literal
                    log.debug("REPLACING! {0} = {1}".format(n, args[n]))
                    statement.second.basic.pop("literal")
                    statement.second["basic"] = args[n]
            statements.append(statement)
        
        log.debug("Populated macro: {0}".format(P.ParseResults(statements).asXML()))
        log.debug(" statement.second = {0}".format(statements[0].second))
        # Do code generation
        code = []
        for s in statements:
            code.extend(generate(s))
        return code
        
    def generate(s):
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
        if x is not None: code.append(x)
        if y is not None: code.append(y)
        return code
    
    for i, line in enumerate(parsed):
        log.debug("Interpreting element {0}: {1}".format(i, line))
        if line.label:
            if line.label in labels:
                # TODO(pwaller): Line indications
                log.fatal("Duplicate label definition! {0}".format(line.label))
                return None
            labels[line.label] = len(program)
            
        s = line.statement
        if not s: continue
        
        if s.macro_definition:
            process_macro_definition(s.macro_definition)
            continue
        elif s.macro_call:
            program.extend(process_macro_call(s.macro_call))
            continue
        
        program.extend(generate(s))
        
    # Substitute labels
    for i, c in enumerate(program):
        if isinstance(c, basestring):
            program[i] = labels[c]
    
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
        if not DEBUG: handler.setLevel(logging.INFO)
    
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
        print(program)
    else:
        with open(args.destination, "wb") as fd:
            fd.write(program)
        log.info("Program written to {0} ({1} bytes, hash={2})"
                 .format(args.destination, len(program),
                         hex(abs(hash(program)))))
            
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
