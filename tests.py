import nose.tools as nose
import os
import subprocess


ASSEMBLY_OUTPUT = "__test_output.obj"
SOURCE_DIR = "examples"
BINARY_DIR = "test_binaries"


def tearDownModule():
    if os.path.exists(ASSEMBLY_OUTPUT):
        os.remove(ASSEMBLY_OUTPUT)


def example(name):
    return os.path.join(SOURCE_DIR, name + ".asm")


def check_path(assembler, path):
    code = subprocess.call([assembler, path, ASSEMBLY_OUTPUT])
    nose.assert_equal(code, 0, "Assembly of {0} failed!".format(path))

    assert path.endswith(".asm")
    binary = os.path.join(BINARY_DIR, os.path.basename(path)[:-4] + ".bin")
    if os.path.exists(binary):
        with open(ASSEMBLY_OUTPUT, "rb") as testing, open(binary, "rb") as tested:
            nose.assert_equal(testing.read(), tested.read(), "Produced and tested binaries differ!")


# asm.py
def test_example_asm():
    check_path("./asm.py", "example.asm")


def test_hello_asm():
    check_path("./asm.py", example("hello"))


def test_hello2_asm():
    check_path("./asm.py", example("hello2"))


def test_fibonacci_asm():
    check_path("./asm.py", example("ique_fibonacci"))


# asm_pyparsing.py
def test_example_pyparsing():
    check_path("./asm_pyparsing.py", "example.asm")


def test_hello_pyparsing():
    check_path("./asm_pyparsing.py", example("hello"))


def test_hello2_pyparsing():
    check_path("./asm_pyparsing.py", example("hello2"))


def test_fibonacci_pyparsing():
    check_path("./asm_pyparsing.py", example("ique_fibonacci"))
