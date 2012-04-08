# A Python implementation of Notch's DCPU-16.

Complete with assembler, disassembler, debugger and video terminal implementations.

See http://0x10c.com/doc/dcpu-16.txt for specification of the CPU.

Notch apparently started doing a 6502 emulator first. Given I did one in
Python <https://github.com/jtauber/applepy> it only seems fitting I now
do a DCPU-16 implementation in Python too :-)


## Status

Runs a number of example programs successfully. Should be feature-complete at the CPU level.

A dissassembler and (two) assemblers are also included as well as the emulator. The emulator
includes a debugger. 

* `./asm.py example.asm example.obj` will assemble Notch's example to object code
* `./disasm.py example.obj` will disassemble the given object code
* `./dcpu16.py example.obj` will execute it (but won't show anything without extra options)

There is also an experimental pyparsing-based assembler `./asm_pyparsing.py`
contributed by Peter Waller. You'll need to `pip install pyparsing` to run it.

`./dcpu16.py` takes a number of options:

* `--debug` runs the emulate in debug mode, enabling you to step through each instruction
* `--trace` dumps the registers and stack after every step (implied by `--debug`)
* `--speed` outputs the speed the emulator is running at in kHz
* `--term TERM` specifies a terminal to use for text output (`null`, `debug`, `curses`, `pygame` or `qt`)

I plan to work on an implementation of Forth on the DCPU-16 soon. Colour terminals and keyboard
support are also planned.


## Examples

Now see [https://github.com/jtauber/DCPU-16-Examples](https://github.com/jtauber/DCPU-16-Examples)
(although my assembler and emulator don't necessarily support everything there yet)