# A Python implementation of Notch's DCPU-16.

See http://0x10c.com/doc/dcpu-16.txt for specification.

Notch apparently started doing a 6502 emulator first. Given I did one in
Python <https://github.com/jtauber/applepy> it only seems fitting I now
do a DCPU-16 implementation in Python too :-)


## Status

Runs the example program successfully. Cycle times are not yet taken
into account but it otherwise should be feature-complete.

A dissassembler and assembler are also included.

* `./asm.py example.asm example.obj` will assemble Notch's example to object code
* `./dcpu16.py example.obj` will execute it (currently hard-coded to debug mode)
* `./disasm.py example.obj` will disassemble the given object code

There is also an experimental pyparsing-based assembler ./asm_pyparsing.py
contributed by Peter Waller with support for case-insensitive instructions and
identifers as well as `dat`.

Note that the disassembler doesn't quite output in a format that can be
round-tripped back into the assembler as it annotates each line with a
memory offset.

I plan to work on a Forth implementation soon.

I'm also keen to find out how Notch plans I/O to work.


## Examples

Now see [https://github.com/jtauber/DCPU-16-Examples](https://github.com/jtauber/DCPU-16-Examples) (almost my assembler and
emulator don't necessarily support everything there yet)