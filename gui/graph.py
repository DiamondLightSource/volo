from PyQt5.QtWidgets import QApplication, QMainWindow, QGroupBox, QWidget
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QGridLayout
from PyQt5.QtWidgets import QSpacerItem, QLineEdit
from PyQt5.QtGui import QPainter, QDrag, QDoubleValidator, QValidator
from PyQt5.QtCore import Qt, QMargins, QMimeData
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import os
import sys
import at
import at.plot
import numpy
from collections import OrderedDict
import atip.ease as e
import math


class Window(QMainWindow):
    def __init__(self, parent=None):
        super(Window, self).__init__(parent)
        lattice = e.loader()
        self.lattice = e.get_sim_ring(lattice)
        self._atsim = e.get_atsim(lattice)
        self.s_selection = None
        self.total_len = sum([elem.Length for elem in self.lattice])
        self.n = 1
        if self.n is not None:
            superperiod_len = self.total_len / 6.0
            superperiod_bounds = superperiod_len * numpy.array(range(7))
            self.lattice.s_range = superperiod_bounds[self.n-1:self.n+1]
            self.total_len = self.lattice.s_range[1] - self.lattice.s_range[0]
        self.initUI()

    def initUI(self):
        self.setGeometry(0, 0, 1500, 800)
        # initialise layouts
        layout = QHBoxLayout()
        layout.setSpacing(20)
        self.left_side = QVBoxLayout()
        self.left_side.setAlignment(Qt.AlignLeft)

        # create graph
        graph = QHBoxLayout()
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)
        self.canvas.mpl_connect('button_press_event', self.graph_onclick)
        self.plot()
        self.canvas.setMinimumWidth(1000)
        self.canvas.setMinimumHeight(480)
        self.canvas.setMaximumHeight(480)
        self.graph_width = 1000
        self.figure.set_tight_layout({"pad": 0.5, "w_pad": 0, "h_pad": 0})
        graph.addWidget(self.canvas)
        self.left_side.addLayout(graph)
        # data3.setToolTip("m")
        # border-bottom-width:1px;border-bottom-style:solid; border-radius:0px

        # create lattice representation bar
        self.lat_disp = QHBoxLayout()
        self.lat_disp.setSpacing(0)
        self.lat_disp.setContentsMargins(QMargins(0, 0, 0, 0))
        self.lat_disp.addStretch()
        self.lat_disp.addWidget(element_repr(-1, 1, Qt.black))
        self.lat_repr = self.create_lat_repr()
        for el in self.lat_repr:
            self.lat_disp.addWidget(el)
        self.lat_disp.addWidget(element_repr(-1, 1, Qt.black))
        self.lat_disp.addStretch()
        self.left_side.addLayout(self.lat_disp)

        # create elem editing boxes to drop to
        bottom = QHBoxLayout()
        bottom.addWidget(edit_box(self.lattice))
        bottom.addWidget(edit_box(self.lattice))
        bottom.addWidget(edit_box(self.lattice))
        bottom.addWidget(edit_box(self.lattice))
        self.left_side.addLayout(bottom)
        self.left_side.addStretch()

        # all components now set add to main layout
        layout.addLayout(self.left_side)

        # create lattice and element data sidebar
        sidebar = QGridLayout()
        sidebar.setSpacing(10)
        self.lattice_data_widgets = {}
        if self.n is None:
            title = QLabel("Global Lattice Parameters:")
        else:
            title = QLabel("Global Super Period Parameters:")
        title.setMaximumWidth(220)
        title.setMinimumWidth(220)
        title.setStyleSheet("font-weight:bold; text-decoration:underline")
        sidebar.addWidget(title, 0, 0)
        spacer = QLabel("")
        spacer.setMaximumWidth(220)
        spacer.setMinimumWidth(220)
        sidebar.addWidget(spacer, 0, 1)
        row_count = 1
        for field, value in self.get_lattice_data().items():
            val_str = self.stringify(value)
            sidebar.addWidget(QLabel("{0}: ".format(field)), row_count, 0)
            lab = QLabel(val_str)
            sidebar.addWidget(lab, row_count, 1)
            self.lattice_data_widgets[field] = lab
            row_count += 1
        self.element_data_widgets = {}
        title = QLabel("Selected Element Parameters:")
        title.setStyleSheet("font-weight:bold; text-decoration:underline")
        sidebar.addWidget(title, row_count, 0)
        row_count += 1
        for field, value in self.get_element_data(0).items():
            sidebar.addWidget(QLabel("{0}: ".format(field)), row_count, 0)
            lab = QLabel("N/A")
            sidebar.addWidget(lab, row_count, 1)
            self.element_data_widgets[field] = lab
            row_count += 1
        # Add units tool tips
        self.lattice_data_widgets["Total Length"].setToolTip("m")
        self.lattice_data_widgets["Horizontal Emittance"].setToolTip("pm")
        self.lattice_data_widgets["Linear Dispersion Action"].setToolTip("m")
        self.lattice_data_widgets["Energy Loss per Turn"].setToolTip("eV")
        self.lattice_data_widgets["Damping Times"].setToolTip("msec")
        self.lattice_data_widgets["Total Bend Angle"].setToolTip("deg")
        self.lattice_data_widgets["Total Absolute Bend Angle"].setToolTip("deg")
        self.element_data_widgets["Selected S Position"].setToolTip("m")
        self.element_data_widgets["Element Start S Position"].setToolTip("m")
        self.element_data_widgets["Element Length"].setToolTip("m")
        self.element_data_widgets["Horizontal Linear Dispersion"].setToolTip("m")
        self.element_data_widgets["Beta Function"].setToolTip("m")
        layout.addLayout(sidebar)

        # set layout
        wid = QWidget(self)
        wid.setLayout(layout)
        self.setCentralWidget(wid)
        self.setStyleSheet("background-color:white")
        self.show()

    def create_lat_repr(self):
        lat_repr = []
        self.base_widths = []
        for elem in self.lattice[:415]:
            width = math.ceil(elem.Length)
            if width != 0:
                self.base_widths.append(elem.Length)
                if isinstance(elem, at.elements.Drift):
                    elem_repr = element_repr(elem.Index, width, Qt.white)
                elif isinstance(elem, at.elements.Dipole):
                    elem_repr = element_repr(elem.Index, width, Qt.green)
                elif isinstance(elem, at.elements.Quadrupole):
                    elem_repr = element_repr(elem.Index, width, Qt.red)
                elif isinstance(elem, at.elements.Sextupole):
                    elem_repr = element_repr(elem.Index, width, Qt.yellow)
                else:
                    elem_repr = element_repr(elem.Index, width, Qt.blue)
                lat_repr.append(elem_repr)
        return lat_repr

    def calc_new_width(self, new_width):
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
        return scaled_widths

    def get_lattice_data(self):
        data_dict = OrderedDict()
        data_dict["Number of Elements"] = len(self.lattice.i_range)
        data_dict["Total Length"] = self.total_len
        data_dict["Cell Tune"] = [self._atsim.get_tune(0),
                                  self._atsim.get_tune(1)]
        data_dict["Linear Chromaticity"] = [self._atsim.get_chrom(0),
                                            self._atsim.get_chrom(1)]
        data_dict["Horizontal Emittance"] = self._atsim.get_emit(0) * 1e12
        data_dict["Linear Dispersion Action"] = 0.0
        data_dict["Momentum Spread"] = 0.0
        data_dict["Linear Momentum Compaction"] = self._atsim.get_mcf()
        data_dict["Energy Loss per Turn"] = self._atsim.get_energy_loss()
        data_dict["Damping Times"] = self._atsim.get_damping_times() * 1e3
        data_dict["Damping Partition Numbers"] = [0, 0, 0]
        data_dict["Total Bend Angle"] = self._atsim.get_total_bend_angle()
        data_dict["Total Absolute Bend Angle"] = self._atsim.get_total_absolute_bend_angle()
        return data_dict

    def get_element_data(self, selected_s_pos):
        data_dict = OrderedDict()
        all_s = self._atsim.get_s()
        index = int(numpy.where([s <= selected_s_pos for s in all_s])[0][-1])
        data_dict["Selected S Position"] = selected_s_pos
        data_dict["Element Index"] = index + 1
        data_dict["Element Start S Position"] = all_s[index]
        data_dict["Element Length"] = self._atsim.get_at_element(index+1).Length
        data_dict["Horizontal Linear Dispersion"] = self._atsim.get_disp()[index, 0]
        data_dict["Beta Function"] = self._atsim.get_beta()[index]
        data_dict["Derivative of Beta Function"] = self._atsim.get_alpha()[index]
        data_dict["Normalized Phase Advance"] = self._atsim.get_mu()[index]/(2*numpy.pi)
        return data_dict

    def stringify(self, value):
        v = []
        if numpy.issubdtype(type(value), numpy.number):
            value = [value]
        for val in value:
            if isinstance(val, int):
                v.append("{0:d}".format(val))
            else:
                if val == 0:
                    v.append("0.0")
                elif abs(val) < 0.1:
                    v.append("{0:.5e}".format(val))
                else:
                    v.append("{0:.5f}".format(val))
        if len(v) == 1:
            return v[0]
        else:
            return "[" + ', '.join(v) + "]"

    def update_lattice_data(self):
        for field, value in self.get_lattice_data().items():
            val_str = self.stringify(value)
            self.lattice_data_widgets[field].setText(val_str)

    def update_element_data(self, s_pos):
        for field, value in self.get_element_data(s_pos).items():
            val_str = self.stringify(value)
            self.element_data_widgets[field].setText(val_str)

    def plot(self):
        self.lattice.radiation_off()
        self.figure.clear()
        self.axl = self.figure.add_subplot(111, xmargin=0, ymargin=0.025)
        self.axl.set_xlabel('s position [m]')
        self.axr = self.axl.twinx()
        self.axr.margins(0, 0.025)
        at.plot.plot_beta(self.lattice, axes=(self.axl, self.axr))
        self.canvas.draw()

    def graph_onclick(self, event):
        if event.xdata is not None:
            if self.s_selection is not None:
                self.s_selection.remove()
                for lab in self.element_data_widgets.values():
                    lab.setText("N/A")
            if event.button == 1:
                self.s_selection = self.axl.axvline(event.xdata, color="black",
                                                    linestyle='--', zorder=3)
                self.update_element_data(event.xdata)
            else:
                self.s_selection = None
            self.canvas.draw()
            self.resize_graph(self.graph_width, True)
        """
        print('%s click: button=%d, x=%d, y=%d, xdata=%f, ydata=%f' %
              ('double' if event.dblclick else 'single', event.button,
               event.x, event.y, event.xdata, event.ydata))
        """

    def resize_graph(self, width, redraw=False):
        if (int(width) != int(self.graph_width)) or redraw:
            # dpi = self.figure.dpi
            self.canvas.flush_events()
            # self.figure.set_size_inches(width/dpi, 480/dpi, forward=True)
            self.canvas.resize(width, 480)
            self.graph_width = width

    def resizeEvent(self, event):
        width = int(max([self.frameGeometry().width() - 500, 1000]))
        self.resize_graph(width)
        widths = self.calc_new_width(width - 125)
        for el, w in zip(self.lat_repr, widths):
            el.changeSize(w)
        super().resizeEvent(event)


class element_repr(QWidget):
    def __init__(self, index, width, colour):
        super().__init__()
        self.index = index
        self.width = width
        self.colour = colour
        self.setMinimumHeight(100)
        self.setMinimumWidth(width)

    def paintEvent(self, event):
        qp = QPainter(self)
        qp.setPen(self.colour)
        qp.setBrush(self.colour)
        qp.drawRect(0, 0, self.width, 100)

    def changeSize(self, width, height=None):
        self.width = width
        self.setMinimumWidth(width)
        self.repaint()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            mimeData = QMimeData()
            mimeData.setText(str(self.index))
            drag = QDrag(self)
            drag.setMimeData(mimeData)
            drag.exec(Qt.MoveAction)  # dropAction =
        return


class edit_box(QGroupBox):
    def __init__(self, lattice):
        super().__init__()
        self.lattice = lattice
        self.setMaximumSize(300, 200)
        self.setAcceptDrops(True)
        self.dl = self.create_box()

    def create_box(self):
        data_labels = {}
        grid = QGridLayout()
        float_validator = QDoubleValidator()
        float_validator.setNotation(QDoubleValidator.StandardNotation)
        pass_validator = PassMethodValidator()
        data_labels["Index"] = QLabel("N/A")
        grid.addWidget(QLabel("Index"), 0, 0)
        grid.addWidget(data_labels["Index"], 0, 1)
        data_labels["Type"] = QLabel("N/A")
        grid.addWidget(QLabel("Type"), 1, 0)
        grid.addWidget(data_labels["Type"], 1, 1)
        data_labels["Length"] = QLineEdit("")
        data_labels["Length"].setAcceptDrops(False)
        data_labels["Length"].setValidator(float_validator)
        grid.addWidget(QLabel("Length"), 2, 0)
        grid.addWidget(data_labels["Length"], 2, 1)
        data_labels["PassMethod"] = QLineEdit("")
        data_labels["PassMethod"].setAcceptDrops(False)
        data_labels["PassMethod"].setValidator(pass_validator)
        grid.addWidget(data_labels["PassMethod"], 3, 1)
        grid.addWidget(QLabel("PassMethod"), 3, 0)
        data_labels["SetPoint"] = (QLabel("Set Point"), QLineEdit("N/A"))
        data_labels["SetPoint"][1].setAcceptDrops(False)
        data_labels["SetPoint"][1].setValidator(float_validator)
        grid.addWidget(data_labels["SetPoint"][1], 5, 1)
        grid.addWidget(data_labels["SetPoint"][0], 5, 0)
        self.setLayout(grid)
        return data_labels

    def dragEnterEvent(self, event):
        if event.mimeData().text().isdigit():
            event.accept()
        else:  # Reject all but positive integers.
            event.ignore()

    def dropEvent(self, event):
        element = self.lattice[int(event.mimeData().text()) - 1]
        self.dl["Index"].setText(event.mimeData().text())
        self.dl["Type"].setText(element.Class)
        self.dl["Length"].setText(str(element.Length))
        self.dl["PassMethod"].setText(element.PassMethod)
        if isinstance(element, at.elements.Drift):
            self.dl["SetPoint"][0].setText("Set Point Field")
            self.dl["SetPoint"][1].setText("N/A")
        elif isinstance(element, at.elements.Bend):
            self.dl["SetPoint"][0].setText("BendingAngle")
            self.dl["SetPoint"][1].setText(str(element.BendingAngle))
        elif isinstance(element, at.elements.Corrector):
            self.dl["SetPoint"][0].setText("KickAngle")
            self.dl["SetPoint"][1].setText(str(element.KickAngle))
        elif isinstance(element, at.elements.Sextupole):
            self.dl["SetPoint"][0].setText("H")
            self.dl["SetPoint"][1].setText(str(element.H))
        elif isinstance(element, at.elements.Quadrupole):
            self.dl["SetPoint"][0].setText("K")
            self.dl["SetPoint"][1].setText(str(element.K))
        else:  # Drift or unsupported type.
            pass
        event.accept()


class PassMethodValidator(QValidator):
    def __init__(self):
        super().__init__()

    def validate(self, string, pos):
        if (len(string) > 0) and (not string.isalnum()):
            return (QValidator.Invalid, string, pos)
        elif string.endswith("Pass"):
            file_name = at.load.utils.get_file_name(string)
            file_path = os.path.join(at.integrators.__path__[0], file_name)
            if os.path.isfile(os.path.realpath(file_path)):
                return (QValidator.Acceptable, string, pos)
            else:
                return (QValidator.Invalid, string, pos)
        else:
            return (QValidator.Intermediate, string, pos)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Window()
    sys.exit(app.exec_())
