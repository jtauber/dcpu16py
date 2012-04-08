import nose.tools as nose
import os
import subprocess


ASSEMBLY_OUTPUT = "__test_output.obj"
SOURCE_DIR = "examples"

def teardown():
    if os.path.exists(ASSEMBLY_OUTPUT):
        os.remove(ASSEMBLY_OUTPUT)

def example(name):
    return os.path.join(SOURCE_DIR, name + ".asm")

def check_asm(path):
    code = subprocess.call(["./asm.py", path, ASSEMBLY_OUTPUT])
    nose.assert_equal(code, 0, "(asm.py)")

def check_pyparsing(path):
    code = subprocess.call(["./asm_pyparsing.py", path, ASSEMBLY_OUTPUT])
    nose.assert_equal(code, 0, "(asm_pyparsing.py)")


# asm.py
@nose.with_setup(teardown=teardown)
def test_example_asm():
    check_asm("example.asm")

@nose.with_setup(teardown=teardown)
def test_hello_asm():
    check_asm(example("hello"))

@nose.with_setup(teardown=teardown)
def test_hello2_asm():
    check_asm(example("hello2"))

@nose.with_setup(teardown=teardown)
def test_fibonacci_asm():
    check_asm(example("ique_fibonacci"))

# asm_pyparsing.py
@nose.with_setup(teardown=teardown)
def test_example_pyparsing():
    check_pyparsing("example.asm")

@nose.with_setup(teardown=teardown)
def test_hello_pyparsing():
    check_pyparsing(example("hello"))

@nose.with_setup(teardown=teardown)
def test_hello2_pyparsing():
    check_pyparsing(example("hello2"))

@nose.with_setup(teardown=teardown)
def test_fibonacci_pyparsing():
    check_pyparsing(example("ique_fibonacci"))
