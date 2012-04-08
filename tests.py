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

def check_source(path):
    code = subprocess.call(["./asm.py", path, ASSEMBLY_OUTPUT])
    nose.assert_equal(code, 0)
    code = subprocess.call(["./asm_pyparsing.py", path, ASSEMBLY_OUTPUT])
    nose.assert_equal(code, 0)


@nose.with_setup(teardown=teardown)
def test_hello():
    check_source(example("hello"))

@nose.with_setup(teardown=teardown)
def test_example():
    check_source("example.asm")
