import threading
import glob, imp
from os.path import join, basename, splitext

PLUGINS_DIR = "./plugins/"

def importPlugins(dir = PLUGINS_DIR):
    # http://tinyurl.com/cfceawr
    return [_load(path).plugin for path in glob.glob(join(dir,'[!_]*.py'))]

def _load(path):
    # http://tinyurl.com/cfceawr
    name, ext = splitext(basename(path))
    return imp.load_source(name, path)
    

class BasePlugin:
    """
        Plugin module to interface with a cpu core.

        
        Signaling a shutdown should be done via raising SystemExit within tick()
    """
    
    # Specify if you want to use a different name class name
    name = None
    
    # List in the format of [(*args, *kwargs)]
    arguments = []
    
    # Set in __init__ if you do not wish to have been "loaded" or called
    loaded = True
    
    def tick(self, cpu):
        """
            Gets called at the end of every cpu tick
        """
        pass
    
    def shutdown(self):
        """
            Gets called on shutdown of the emulator
        """
        pass
    
    def memory_changed(self, cpu, address, value):
        """
            Gets called on a write to memory
        """
        pass
    
    def __init__(self, args=None):
        self.name = self.__class__.__name__ if not self.name else self.name

# Assign this to your plugin class
plugin = None
