from PyQt5.QtWidgets import QApplication, QMainWindow, QGroupBox, QWidget
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QGridLayout, QSpacerItem, QSizePolicy
from PyQt5.QtGui import QPixmap, QPainter, QColor, QBrush
from PyQt5.QtCore import Qt, QRect, QMargins

import sys
import at
import numpy
import atip.ease as e
import math
import time

class Window(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        layout = QHBoxLayout()
        p = element_repr(0.5, Qt.red)
        #layout.addStretch()
        layout.addWidget(p)
        #layout.addStretch()
        wid = QWidget(self)
        wid.setLayout(layout)
        self.setCentralWidget(wid)
        self.setWindowTitle('Colours')
        self.show()

class element_repr(QWidget):
    def __init__(self, width, colour):
        super().__init__()
        self.setMinimumHeight(100)
        self.setMinimumWidth(width)
        self.width = width
        self.colour = colour
        #self.setStyleSheet('QFrame {background-color:grey;}')

    def paintEvent(self, e):
        qp = QPainter(self)
        qp.setPen(self.colour)
        qp.setBrush(self.colour)
        qp.drawRect(0, 0, self.width, 100)

        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Window()
    sys.exit(app.exec_())
