from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout
from PyQt5.QtGui import QPainter
from PyQt5.QtCore import Qt
import sys


class Window(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()

    def initUI(self):
        layout = QHBoxLayout()
        p = element_repr(1000, Qt.red)
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
        self.setMinimumHeight(480)
        self.setMinimumWidth(width)
        self.width = width
        self.colour = colour
        #self.setStyleSheet('QFrame {background-color:grey;}')

    def paintEvent(self, e):
        qp = QPainter(self)
        qp.setPen(self.colour)
        qp.setBrush(self.colour)
        qp.drawRect(0, 0, self.width, 350)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Window()
    sys.exit(app.exec_())
