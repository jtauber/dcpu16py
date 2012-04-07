import sys
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt


class Terminal(QtGui.QWidget):
    VSIZE = 25
    HSIZE = 80
    HEIGHT = 378
    WIDTH = 644
    BUFFER_SIZE = VSIZE * HSIZE
    START_ADDRESS = 0x8000
    
    def __init__(self):
        self.app = QtGui.QApplication(sys.argv)
        super(Terminal, self).__init__()
        
        self.buffer = []
        for y in range(self.VSIZE):
            self.buffer.append([])
            for _ in range(self.HSIZE):
                self.buffer[y].append(" ")
        
        self.font = QtGui.QFont("Monospace", 10)
        self.font.setStyleHint(QtGui.QFont.TypeWriter)
        font_metrics = QtGui.QFontMetrics(self.font)
        self.width = font_metrics.maxWidth() * self.HSIZE + 4
        self.height = font_metrics.height() * self.VSIZE + 4
        
        self.resize(self.width, self.height)
        self.setMinimumSize(self.width, self.height)
        self.setMaximumSize(self.width, self.height)
        self.setWindowTitle("DCPU-16 terminal")
    
    def update_memory(self, address, value):
        if self.START_ADDRESS <= address < (self.START_ADDRESS + self.VSIZE * self.HSIZE):
            index = address - self.START_ADDRESS
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
        
        qp.fillRect(0, 0, self.width, self.height, QtGui.QBrush(QtGui.QColor(0, 0, 0)))
        
        text = "\n".join("".join(line) for line in self.buffer)
        qp.setPen(QtGui.QColor(255, 255, 255))
        qp.setFont(self.font)
        qp.drawText(1, 1, self.width, self.height, Qt.AlignLeft | Qt.AlignTop, text)        
        
        qp.end()
