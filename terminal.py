import sys
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt


class Terminal(QtGui.QWidget):
    VSIZE = 25
    HSIZE = 80
    HEIGHT = 378
    WIDTH = 644
    BUFFER_SIZE = VSIZE * HSIZE
    
    def __init__(self):
        self.app = QtGui.QApplication(sys.argv)
        super(Terminal, self).__init__()
        self.buffer = []
        for y in range(self.VSIZE):
            self.buffer.append([])
            for _ in range(self.HSIZE):
                self.buffer[y].append(" ")
        self.resize(self.WIDTH, self.HEIGHT)
        self.setWindowTitle("DCPU-16 terminal")
    
    def update_buffer(self, location, value):
        index = location - 0x8000
        line = index // self.HSIZE
        col = index % self.HSIZE
        char = chr(value & 0x00FF)
        self.buffer[line][col] = char
    
    def redraw(self):
        self.update()
        self.app.processEvents()
    
    def quit(self):
        self.app.quit()
    
    def paintEvent(self, event):
        qp = QtGui.QPainter()
        qp.begin(self)
        
        qp.fillRect(0, 0, self.WIDTH, self.HEIGHT, QtGui.QBrush(QtGui.QColor(0, 0, 0)))
        
        text = "\n".join("".join(line) for line in self.buffer)
        qp.setPen(QtGui.QColor(255, 255, 255))
        qp.setFont(QtGui.QFont("Monospace", 10))
        qp.drawText(1, 1, self.WIDTH, self.HEIGHT, Qt.AlignLeft | Qt.AlignTop, text)        
        
        qp.end()
