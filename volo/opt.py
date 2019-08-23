import os
import sys
from collections import OrderedDict
from functools import partial

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
        # Set initial window size and layout
        self.setGeometry(0, 0, 500, 500)
        layout = QVBoxLayout()

        # Create variables section
        self.variables = None
        self.variable_list = []
        self.vars_box = QGridLayout()
        self.add_variable(True)
        title = QLabel("Variables:")
        title.setStyleSheet("font-weight:bold")
        self.vars_box.addWidget(title, 0, 0)
        self.add_var_button = QPushButton("Add Variable")
        self.add_var_button.setCheckable(True)
        self.add_var_button.clicked.connect(self.add_variable)
        self.vars_box.addWidget(self.add_var_button, 0, 3)
        subtitle1 = QLabel("index:")
        subtitle1.setStyleSheet("text-decoration:underline;")
        self.vars_box.addWidget(subtitle1, 1, 0)
        subtitle2 = QLabel("field:")
        subtitle2.setStyleSheet("text-decoration:underline;")
        self.vars_box.addWidget(subtitle2, 1, 1)
        subtitle3 = QLabel("cell:")
        subtitle3.setStyleSheet("text-decoration:underline;")
        self.vars_box.addWidget(subtitle3, 1, 2)
        subtitle4 = QLabel("value:")
        subtitle4.setStyleSheet("text-decoration:underline;")
        self.vars_box.addWidget(subtitle4, 1, 3)
        self.add_variable_box()
        layout.addLayout(self.vars_box)

        # Set and display layout
        wid = QWidget(self)
        wid.setLayout(layout)
        self.setCentralWidget(wid)
        self.show()

    def add_variable_box(self):
        row_count = 2
        for variable in self.variable_list:
            index, field, cell, value = variable
            self.vars_box.addWidget(index, row_count, 0)
            self.vars_box.addWidget(field, row_count, 1)
            self.vars_box.addWidget(cell, row_count, 2)
            self.vars_box.addWidget(value, row_count, 3)
            row_count += 1

    def add_variable(self, init=False):
        if not init:
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
            index = QLineEdit()
            field = QComboBox()
            cell = QComboBox()
            value = QLineEdit()
            field.setSizeAdjustPolicy(0)
            field.currentTextChanged.connect(partial(self.var_field, index,
                                                     cell))
            cell.currentTextChanged.connect(partial(self.var_cell, index,
                                                    field, value))
            index.textChanged.connect(partial(self.var_index,
                                              field, cell, value))
            self.variable_list.append((index, field, cell, value))
            self.add_variable_box()
        else:
            print("If you really need > 25 variable use the terminal client.")

    def var_index(self, field_box, cell_box, value_box, index):
        ignored_fields = ['FamName', 'PassMethod', 'Class', 'Index',
                          'R1', 'R2', 'T1', 'T2']
        elem = self.lattice[int(index)]
        fields = []
        for key, value in vars(elem).items():
            if key not in ignored_fields:
                if isinstance(value, numpy.ndarray):
                    if numpy.issubdtype(value.dtype, numpy.number):
                        fields.append(key)
                elif numpy.issubdtype(type(value), numpy.number):
                    fields.append(key)
        self.update_combo_box(field_box, fields)

    def var_field(self, index_box, cell_box, field):
        elem = self.lattice[int(index_box.text())]
        if field != '':
            value = vars(elem)[field]
            if isinstance(value, numpy.ndarray):
                if len(value.shape) == 1:
                    if len(value) == 1:
                        self.update_combo_box(cell_box, [''])
                    else:
                        self.update_combo_box(cell_box, [str(c) for c in
                                                         range(len(value))])
                else:
                    raise MemoryError("I know this is possible, I just don't "
                                      "have the time to figure it out now.")
            else:
                self.update_combo_box(cell_box, [''])

    def update_combo_box(self, box, items):
        for i in range(box.count()):
            box.removeItem(i)
        box.addItems(items)

    def var_cell(self, index_box, field_box, value_box, cell):
        elem = self.lattice[int(index_box.text())]
        if cell == '':
            value_box.setText(str(vars(elem)[field_box.currentText()]))
        else:
            print(cell, vars(elem)[field_box.currentText()])
            value_box.setText(str(vars(elem)[field_box.currentText()][int(cell)]))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Window()
    sys.exit(app.exec_())
