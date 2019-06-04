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
        lattice = e.loader()
        self.lattice = e.get_sim_ring(lattice)
        self.initUI()

    def initUI(self):
        self.layout = QHBoxLayout()
        self.layout.setSpacing(0)
        self.layout.addStretch()
        self.lat_repr = self.create_lat_repr()
        widths = self.calc_new(880)
        for el, w in zip(self.lat_repr, widths):
            el.changeSize(w)
            self.layout.addWidget(el)
        self.layout.addStretch()
        self.wid = QWidget(self)
        self.wid.setLayout(self.layout)
        self.wid.setMinimumHeight(120)
        self.setCentralWidget(self.wid)
        self.show()

    def create_lat_repr(self):
        lat_repr = []
        self.base_widths = []
        for elem in self.lattice[:415]:
            width = math.ceil(elem.Length)
            self.base_widths.append(elem.Length)
            if width != 0:
                if isinstance(elem, at.elements.Drift):
                    elem_repr = element_repr(width, Qt.white)
                elif isinstance(elem, at.elements.Dipole):
                    elem_repr = element_repr(width, Qt.green)
                elif isinstance(elem, at.elements.Quadrupole):
                    elem_repr = element_repr(width, Qt.red)
                elif isinstance(elem, at.elements.Sextupole):
                    elem_repr = element_repr(width, Qt.yellow)
                else:
                    elem_repr = element_repr(width, Qt.blue)
                lat_repr.append(elem_repr)
        #self.tot_len = sum(self.base_widths)
        return lat_repr

    def calc_new(self, new_width):
        t1 = time.time()
        scale_factor = new_width / sum(self.base_widths)
        scaled_widths = [width * scale_factor for width in self.base_widths]
        rounding = []
        for index in range(len(scaled_widths)):
            if scaled_widths[index] == 0:
                pass
            elif scaled_widths[index] < 1:
                scaled_widths[index] = 1
            else:
                value = scaled_widths[index]
                scaled_widths[index] = round(value)
                if round(value) >= 2:
                    rounding.append((value, index))
        rounding.sort()  # sort smallest to biggest
        diff = round(sum(scaled_widths) - new_width)
        print(diff, len(rounding))
        if abs(diff) > len(rounding):
            raise ValueError("too many elements with 0<length<1")
        if diff > 0:  # overshoot
            for i in range(diff):
                _, index = rounding.pop()
                scaled_widths[index] = numpy.maximum(scaled_widths[index]-1, 1)
        elif diff < 0:  # undershoot
            for i in range(abs(diff)):
                _, index = rounding.pop(0)
                scaled_widths[index] = scaled_widths[index]+1
        print(time.time()-t1, sum(scaled_widths))
        return scaled_widths

    def calc_new_widths(self, new_width, tot_len):
        scale_factor = new_width / tot_len
        widths = [math.ceil(width*scale_factor) for width in self.base_widths]
        print(scale_factor, sum(widths))
        return widths, sum(widths)

    def resize_repr(self, width):
        if len(self.base_widths) > width:
            raise ValueError("Super Period too large to display.")
        else:
            _, tot_len = self.calc_new_widths(width, sum(self.base_widths))
            print(tot_len)
            var = width / 0.01
            while tot_len < width:
                widths, tot_len = self.calc_new_widths(width, tot_len)
                print(tot_len)
            self.tot_len = sum(widths)
            for el, w in zip(self.lat_repr, widths):
                el.changeSize(w)
            self.wid.setMinimumWidth(self.tot_len)
            self.wid.setMaximumWidth(self.tot_len)
            print(self.tot_len)


class element_repr(QWidget):
    def __init__(self, width, colour):
        super().__init__()
        self.width = width
        self.colour = colour
        #self.setStyleSheet('QFrame {background-color:grey;}')

    def paintEvent(self, e):
        qp = QPainter(self)
        qp.setPen(self.colour)
        qp.setBrush(self.colour)
        qp.drawRect(0, 0, self.width, 100)

    def changeSize(self, width, height=None):
        self.width = width
        self.setMinimumWidth(width)
        self.setMaximumWidth(width)
        self.repaint()

        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Window()
    sys.exit(app.exec_())
