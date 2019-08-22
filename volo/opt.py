import os
import sys
from collections import OrderedDict

import at
import at.plot
import atip
import math
import numpy
import optimizer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PyQt5.QtCore import Qt, QMargins, QMimeData, QEvent
from PyQt5.QtGui import QPainter, QDrag, QDoubleValidator, QValidator
from PyQt5.QtWidgets import (QApplication, QMainWindow, QGroupBox, QWidget,
                             QVBoxLayout, QHBoxLayout, QLabel, QGridLayout,
                             QLineEdit, QComboBox, QPushButton)

class Window(QMainWindow):
    def __init__(self, parent=None):
        super(Window, self).__init__(parent)
        self.lattice = atip.utils.load_at_lattice('DIAD')
        self.initUI()

    def initUI(self):
        self.setGeometry(0, 0, 500, 500)
        layout = QVBoxLayout()
        self.variables = None
        self.variable_list = [(QLineEdit(), QLineEdit(), QLineEdit(),
                               QLineEdit())]
        self.vars_box = QGridLayout()
        title = QLabel("Variables:")
        title.setStyleSheet("font-weight:bold")
        self.vars_box.addWidget(title, 0, 0)
        self.add_var_button = QPushButton("Add Variable")
        self.add_var_button.setCheckable(True)
        self.add_var_button.clicked.connect(self.add_variable)
        self.vars_box.addWidget(self.add_var_button, 0, 3)
        subtitle1 = QLabel("field:")
        subtitle1.setStyleSheet("text-decoration:underline;")
        self.vars_box.addWidget(subtitle1, 1, 0)
        subtitle2 = QLabel("cell:")
        subtitle2.setStyleSheet("text-decoration:underline;")
        self.vars_box.addWidget(subtitle2, 1, 1)
        subtitle3 = QLabel("index:")
        subtitle3.setStyleSheet("text-decoration:underline;")
        self.vars_box.addWidget(subtitle3, 1, 2)
        subtitle4 = QLabel("value:")
        subtitle4.setStyleSheet("text-decoration:underline;")
        self.vars_box.addWidget(subtitle4, 1, 3)
        self.add_variable_box()
        layout.addLayout(self.vars_box)
        wid = QWidget(self)
        wid.setLayout(layout)
        self.setCentralWidget(wid)
        self.show()

    def add_variable_box(self):
        row_count = 2
        for variable in self.variable_list:
            field, cell, index, value = variable
            self.vars_box.addWidget(field, row_count, 0)
            self.vars_box.addWidget(cell, row_count, 1)
            self.vars_box.addWidget(index, row_count, 2)
            self.vars_box.addWidget(value, row_count, 3)
            row_count += 1

    def add_variable(self):
        fields = []
        indices = []
        values = []
        for var in self.variable_list:
            if var[1].text() != '':
                fields.append([var[0].text(), var[1].text()])
            else:
                fields.append(var[0].text())
            indices.append(var[2].text())
            values.append(var[3].text())
        optimizer.Variables(fields, indices, values)
        self.add_var_button.toggle()
        if len(self.variable_list) <= 25:
            self.variable_list.append((QLineEdit(), QLineEdit(), QLineEdit(),
                                       QLineEdit()))
            self.add_variable_box()
        else:
            print("If you really need > 25 variable use the terminal api.")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Window()
    sys.exit(app.exec_())
