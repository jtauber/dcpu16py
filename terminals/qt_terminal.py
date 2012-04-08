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
    
    def __init__(self, args):
        self.width = self.VSIZE
        self.height = self.HSIZE
        self.app = QtGui.QApplication(sys.argv)
        super(Terminal, self).__init__()
        
        self.font = QtGui.QFont("Monospace", 10)
        self.font.setStyleHint(QtGui.QFont.TypeWriter)
        font_metrics = QtGui.QFontMetrics(self.font)
        self.cell_width = font_metrics.maxWidth() + 2
        self.cell_height = font_metrics.height()
        win_width = self.cell_width * self.HSIZE
        win_height = self.cell_height * self.VSIZE

        self.pixmap_buffer = QtGui.QPixmap(win_width, win_height)
        self.pixmap_buffer.fill(Qt.black)
        
        self.resize(win_width, win_height)
        self.setMinimumSize(win_width, win_height)
        self.setMaximumSize(win_width, win_height)
        self.setWindowTitle("DCPU-16 terminal")
        
        self.app.setQuitOnLastWindowClosed(False)
        self.closed = False
    
    def update_character(self, row, column, character, color=None):
        char = chr(character)
        x = column * self.cell_width
        y = row * self.cell_height
        
        qp = QtGui.QPainter(self.pixmap_buffer)
        qp.setFont(self.font)
        if not color or (not color[0] and not color[1]):
            fgcolor = self.COLORS[7]
            bgcolor = self.COLORS[0]
        else:
            fgcolor = self.COLORS[color[0]]
            bgcolor = self.COLORS[color[1]]
        qp.fillRect(x, y, self.cell_width, self.cell_height, QtGui.QColor(*bgcolor))
        qp.setPen(QtGui.QColor(*fgcolor))
        qp.drawText(x, y, self.cell_width, self.cell_height, Qt.AlignCenter, char)
        qp.end()
    
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
        qp = QtGui.QPainter(self)
        qp.drawPixmap(0, 0, self.pixmap_buffer)
        qp.end()
