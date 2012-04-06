import threading

class Plugin(threading.Thread):
    """
        Plugin module to interface with a cpu core.
    
        Access to the cpu core should be done via self.cpu
        
        Signaling a shutdown should be done via raising SystemExit
        
        Implemention should happen within tick(), return tick as often as you like.
    """
    
    cpu = None
    name = None
    
    def tick(self):
        """
            Overload this function to implement your plugin
        """
        raise NotImplementedError
    
    def run(self):
        """
            Gets called once on plugin load and loops until shutdown() is called
        """
        while(True):
            self.tick()

    def __init__(self, cpu):
        self.cpu = cpu
        self.name = self.__class__.__name__ if not self.name else self.name
        threading.Thread.__init__(self)
