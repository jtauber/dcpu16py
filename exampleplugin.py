from emuplugin import Plugin

class ExamplePlugin(Plugin):
    """
        Prints "Hello world" ten times then exits
    """
    
    def tick(self):
        if not self.i % 100000:
            print("Hello world")
        if self.i == 1000000:
            raise SystemExit
        self.i += 1
    
    def __init__(self, cpu):
        self.i = 0
        Plugin.__init__(self, cpu)
