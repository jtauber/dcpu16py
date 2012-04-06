import sys
from PyQt4 import QtGui, QtCore
from PyQt4.QtCore import Qt

# Ensure that the QT application does not try to handle (and spam) the KeyboardInterrupt
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)

class Terminal(QtGui.QWidget):
    VSIZE = 25
    HSIZE = 60
    BUFFER_SIZE = VSIZE * HSIZE
    
    COLORS = [(0,0,0), (255,0,0), (0,255,0), (255,255,0), (0,0,255), (255,0,255), (0, 255, 255), (255, 255, 255)]
    
    def __init__(self):
        self.width = self.VSIZE
        self.height = self.HSIZE
        self.app = QtGui.QApplication(sys.argv)
        super(Terminal, self).__init__()
        
        self.buffer = []
        for y in range(self.VSIZE):
            self.buffer.append([])
            for _ in range(self.HSIZE):
                self.buffer[y].append((" ", None))
        
        self.font = QtGui.QFont("Monospace", 10)
        self.font.setStyleHint(QtGui.QFont.TypeWriter)
        font_metrics = QtGui.QFontMetrics(self.font)
        self.cell_width = font_metrics.maxWidth() + 2
        self.cell_height = font_metrics.height()
        win_width = self.cell_width * self.HSIZE
        win_height = self.cell_height * self.VSIZE
        
        self.resize(win_width, win_height)
        self.setMinimumSize(win_width, win_height)
        self.setMaximumSize(win_width, win_height)
        self.setWindowTitle("DCPU-16 terminal")
        
        self.app.setQuitOnLastWindowClosed(False)
        self.closed = False
    
    def update_character(self, row, column, character, color=None):
        self.buffer[row][column] = (chr(character), color)
    
    def closeEvent(self, e):
        self.closed = True
    
    def redraw(self):
        if self.closed:
            raise SystemExit
        self.update()
        self.app.processEvents()
    
    def quit(self):
        self.app.quit()
    
    def paintEvent(self, event):
        qp = QtGui.QPainter()
        qp.begin(self)
        qp.setFont(self.font)
        y = 0
        for line in self.buffer:
            x = 0
            for c in line:
                if not c[1] or (not c[1][0] and not c[1][1]):
                    fgcolor = self.COLORS[7]
                    bgcolor = self.COLORS[0]
                else:
                    fgcolor = self.COLORS[c[1][0]]
                    bgcolor = self.COLORS[c[1][1]]
                qp.fillRect(x, y, self.cell_width, self.cell_height, QtGui.QColor(*bgcolor))
                qp.setPen(QtGui.QColor(*fgcolor))
                qp.drawText(x, y, self.cell_width, self.cell_height, Qt.AlignCenter | Qt.AlignCenter, c[0])
                x += self.cell_width
            y += self.cell_height
        qp.end()
