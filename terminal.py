import sys
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt


class Terminal(QtGui.QWidget):
    VSIZE = 25
    HSIZE = 80
    HEIGHT = 378
    WIDTH = 644
    
    def __init__(self):
        super(Terminal, self).__init__()
        self.buffer = []
        for y in range(self.VSIZE):
            self.buffer.append([])
            for _ in range(self.HSIZE):
                self.buffer[y].append(" ")
        self.resize(self.WIDTH, self.HEIGHT)
        self.setWindowTitle("DCPU-16 terminal")
        
    def paintEvent(self, event):
        qp = QtGui.QPainter()
        qp.begin(self)
        
        qp.fillRect(0, 0, self.WIDTH, self.HEIGHT, QtGui.QBrush(QtGui.QColor(0, 0, 0)))
        
        text = "\n".join("".join(line) for line in self.buffer)
        qp.setPen(QtGui.QColor(255, 255, 255))
        qp.setFont(QtGui.QFont("Monospace", 10))
        qp.drawText(1, 1, self.WIDTH, self.HEIGHT, Qt.AlignLeft | Qt.AlignTop, text)        
        
        qp.end()


def main():
    app = QtGui.QApplication(sys.argv)
    term = Terminal()
    term.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
