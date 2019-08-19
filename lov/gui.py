import os
import sys
from collections import OrderedDict

import at
import at.plot
import atip
import math
import numpy
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PyQt5.QtCore import Qt, QMargins, QMimeData, QEvent
from PyQt5.QtGui import QPainter, QDrag, QDoubleValidator, QValidator
from PyQt5.QtWidgets import (QApplication, QMainWindow, QGroupBox, QWidget,
                             QVBoxLayout, QHBoxLayout, QLabel, QGridLayout,
                             QLineEdit, QComboBox)


class Window(QMainWindow):
    """Class for the whole window.
    """
    def __init__(self, parent=None):
        """Load and initialise the lattices.
        """
        super(Window, self).__init__(parent)
        # Lattice loading
        ring = atip.utils.load_at_lattice('DIAD')
        sp_len = ring.circumference/6.0
        ring.s_range = [0, sp_len]
        self.lattice = ring[ring.i_range[0]:ring.i_range[-1]]# + [ring[1491]]
        #self.lattice = at.load_tracy('../atip/atip/rings/for_Tobyn.lat')
        for idx, elem in enumerate(self.lattice):
            elem.Index = idx + 1
        self._atsim = atip.simulator.ATSimulator(self.lattice)
        self.s_selection = None

        # Super-period support
        self.total_len = self.lattice.get_s_pos(len(self.lattice))[0]
        self.symmetry = 6
        #self.symmetry = vars(self.lattice).get('periodicity', 1)

        # Create UI
        self.initUI()

    def initUI(self):
        """Low level UI building of the core sections and their components.
        """
        # Set initial window size in pixels
        self.setGeometry(0, 0, 1500, 800)
        # Initialise layouts
        layout = QHBoxLayout()
        layout.setSpacing(20)
        self.left_side = QVBoxLayout()
        self.left_side.setAlignment(Qt.AlignLeft)

        # Create graph
        graph = QHBoxLayout()
        self.figure = Figure()
        self.canvas = FigureCanvasQTAgg(self.figure)
        self.canvas.mpl_connect('button_press_event', self.graph_onclick)
        self.figure.set_tight_layout({"pad": 0.5, "w_pad": 0, "h_pad": 0})
        self.plot()
        # Make graph fixed size to prevent autoscaling
        self.canvas.setMinimumWidth(1000)
        self.canvas.setMaximumWidth(1000)
        self.canvas.setMinimumHeight(480)
        self.canvas.setMaximumHeight(480)
        self.graph_width = 1000
        self.graph_height = 480
        graph.addWidget(self.canvas)
        graph.setStretchFactor(self.canvas, 0)
        # Add graph to left side layout
        self.left_side.addLayout(graph)

        # Create lattice representation bar
        self.full_disp = QVBoxLayout()
        self.full_disp.setSpacing(0)
        self.lat_disp = QHBoxLayout()
        self.lat_disp.setSpacing(0)
        self.lat_disp.setContentsMargins(QMargins(0, 0, 0, 0))
        # Add a stretch at both ends to keep the lattice representation centred
        self.lat_disp.addStretch()
        # Add startline
        self.lat_disp.addWidget(element_repr(-1, Qt.black, 1, drag=False))
        # Add elements
        self.lat_repr = self.create_lat_repr()
        for el_repr in self.lat_repr:
            self.lat_disp.addWidget(el_repr)
        # Add endline
        self.lat_disp.addWidget(element_repr(-1, Qt.black, 1, drag=False))
        # Add a stretch at both ends to keep the lattice representation centred
        self.lat_disp.addStretch()
        # Add non-zero length representation to lattice representation layout
        self.full_disp.addLayout(self.lat_disp)

        # Add horizontal dividing line
        self.black_bar = QHBoxLayout()
        self.black_bar.addStretch()  # Keep it centred
        self.mid_line = element_repr(-1, Qt.black, 1000, height=1, drag=False)
        self.black_bar.addWidget(self.mid_line)
        self.black_bar.addStretch()  # Keep it centred
        self.full_disp.addLayout(self.black_bar)

        # Create zero length element representation bar
        self.zl_disp = QHBoxLayout()
        self.zl_disp.setSpacing(0)
        # Add a stretch at both ends to keep the lattice representation centred
        self.zl_disp.addStretch()
        # Add startline
        self.zl_disp.addWidget(element_repr(-1, Qt.black, 1, drag=False))
        # Add elements
        self.zl_repr = self.calc_zero_len_repr(1000)
        for el_repr in self.zl_repr:
            self.zl_disp.addWidget(el_repr)
        # Add endline
        self.zl_disp.addWidget(element_repr(-1, Qt.black, 1, drag=False))
        # Add a stretch at both ends to keep the lattice representation centred
        self.zl_disp.addStretch()
        # Add zero length representation to lattice representation layout
        self.full_disp.addLayout(self.zl_disp)
        # Add full lattice representation to left side layout
        self.left_side.addLayout(self.full_disp)

        # Create element editing boxes to drop to
        bottom = QHBoxLayout()
        self.edit_boxes = []
        # Future possibility to auto determine number of boxes by window size
        for i in range(4):
            box = edit_box(self, self._atsim)
            self.edit_boxes.append(box)
            bottom.addWidget(box)
        # Add edit boxes to left side layout
        self.left_side.addLayout(bottom)

        # All left side components now set, add them to main layout
        layout.addLayout(self.left_side)

        # Create lattice and element data sidebar
        sidebar_border = QWidget()
        # Dividing line
        sidebar_border.setStyleSheet(".QWidget {border-left: 1px solid black}")
        sidebar = QGridLayout(sidebar_border)
        sidebar.setSpacing(10)
        # Determine correct global title
        if self.symmetry == 1:
            title = QLabel("Global Lattice Parameters:")
        else:
            title = QLabel("Global Super Period Parameters:")
        # Ensure sidebar width remains fixed
        title.setMaximumWidth(220)
        title.setMinimumWidth(220)
        title.setStyleSheet("font-weight:bold; text-decoration:underline;")
        sidebar.addWidget(title, 0, 0)
        # Ensure sidebar width remains fixed
        spacer = QLabel("")
        spacer.setMaximumWidth(220)
        spacer.setMinimumWidth(220)
        sidebar.addWidget(spacer, 0, 1)
        self.lattice_data_widgets = {}
        row_count = 1  # start after global title row
        # Create global fields
        for field, value in self.get_lattice_data().items():
            sidebar.addWidget(QLabel("{0}: ".format(field)), row_count, 0)
            lab = QLabel(self.stringify(value))
            sidebar.addWidget(lab, row_count, 1)
            self.lattice_data_widgets[field] = lab
            row_count += 1
        # Add element title
        title = QLabel("Selected Element Parameters:")
        title.setStyleSheet("font-weight:bold; text-decoration:underline;")
        sidebar.addWidget(title, row_count, 0)
        self.element_data_widgets = {}
        row_count += 1  # continue after element title row
        # Create local fields
        for field, value in self.get_element_data(0).items():
            sidebar.addWidget(QLabel("{0}: ".format(field)), row_count, 0)
            lab = QLabel("N/A")  # default until s selection is made
            sidebar.addWidget(lab, row_count, 1)
            self.element_data_widgets[field] = lab
            row_count += 1
        # Add units tool tips where applicable
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
        # Add sidebar to main window layout
        layout.addWidget(sidebar_border)

        # Set and display layout
        wid = QWidget(self)
        wid.setLayout(layout)
        self.setCentralWidget(wid)
        self.setStyleSheet("background-color:white;")
        self.show()

    def create_lat_repr(self):
        """Create a list of element representations, in the order that they
        appear in the lattice, colour coded according to their type.
        See also: calc_zero_len_repr
        """
        lat_repr = []
        self.zero_length = []
        self.base_widths = []
        for elem in self.lattice:#[:self.lattice.i_range[-1]]:
            width = math.ceil(elem.Length)
            if width == 0:
                if not (isinstance(elem, at.elements.Drift) or
                        isinstance(elem, at.elements.Marker) or
                        isinstance(elem, at.elements.Aperture)):
                    # don't care about zero length drifts, markers or apertures
                    self.zero_length.append(elem)
            else:
                self.base_widths.append(elem.Length)
                if isinstance(elem, at.elements.Drift):
                    elem_repr = element_repr(elem.Index, Qt.white, width)
                elif isinstance(elem, at.elements.Dipole):
                    elem_repr = element_repr(elem.Index, Qt.green, width)
                elif isinstance(elem, at.elements.Quadrupole):
                    elem_repr = element_repr(elem.Index, Qt.red, width)
                elif isinstance(elem, at.elements.Sextupole):
                    elem_repr = element_repr(elem.Index, Qt.yellow, width)
                elif isinstance(elem, at.elements.Corrector):
                    elem_repr = element_repr(elem.Index, Qt.blue, width)
                else:
                    elem_repr = element_repr(elem.Index, Qt.gray, width)
                lat_repr.append(elem_repr)
        return lat_repr

    def calc_new_width(self, new_width):
        """Calculate the new widths of the element representations so that
        they may be dynamically scaled to fit into the new window size, whilst
        remaining roughly proportional to their lengths.
        """
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

    def calc_zero_len_repr(self, width):
        """Create element representations for elements in the lattice with 0
        length, to be displayed below the non-zero length element
        representations.
        See also: create_lat_repr
        """
        scale_factor = width / self.total_len
        all_s = self._atsim.get_s()
        positions = [0.0]
        for elem in self.zero_length:
            positions.append(all_s[elem.Index-1] * scale_factor)
        zero_len_repr = []
        for i in range(1, len(positions), 1):
            gap_length = int(round(positions[i] - positions[i-1]))
            # N.B. zero length gap spacers are not drag-and-drop-able as they
            # are not drifts, however this could potentially be added in future
            # to allow zero length elements to be moved.
            zero_len_repr.append(element_repr(-1, Qt.white, gap_length,
                                              drag=False))
            elem = self.zero_length[i-1]
            if isinstance(elem, at.elements.Monitor):
                elem_repr = element_repr(elem.Index, Qt.magenta, 1)
            elif isinstance(elem, at.elements.RFCavity):
                elem_repr = element_repr(elem.Index, Qt.cyan, 1)
            elif isinstance(elem, at.elements.Corrector):
                elem_repr = element_repr(elem.Index, Qt.blue, 1)
            else:
                elem_repr = element_repr(elem.Index, Qt.gray, 1)
            zero_len_repr.append(elem_repr)
        diff = int(sum([el_repr.width for el_repr in zero_len_repr]) - width)
        if diff < 0:  # undershoot
            # unless the last zero length element is very close to the end of
            # the displayed section this should always occur.
            zero_len_repr.append(element_repr(-1, Qt.white, abs(diff),
                                              drag=False))
        elif diff > 0:  # overshoot
            # this should rarely occur
            # add zero len elem_repr at the end to maintain consistent length
            zero_len_repr.append(element_repr(-1, Qt.white, 0, drag=False))
            while diff > 1:
                for i in range(len(zero_len_repr)):
                    el_repr = zero_len_repr[i]
                    if el_repr.width > 1:
                        el_repr.changeSize(el_repr.width - 1)
                        diff -= 1
                    if diff < 1:
                        break
        else:
            # add zero len elem_repr at the end to maintain consistent length
            zero_len_repr.append(element_repr(-1, Qt.white, 0, drag=False))
        return zero_len_repr

    def get_lattice_data(self):
        """Calculate the global linear optics data for the lattice, and return
        it in a dictionary by its field names.
        """
        self._atsim.wait_for_calculations()
        data_dict = OrderedDict()
        data_dict["Number of Elements"] = len(self.lattice)
        data_dict["Total Length"] = self.total_len
        data_dict["Total Bend Angle"] = self._atsim.get_total_bend_angle()
        data_dict["Total Absolute Bend Angle"] = self._atsim.get_total_absolute_bend_angle()
        data_dict["Cell Tune"] = [self._atsim.get_tune('x'),
                                  self._atsim.get_tune('y')]
        data_dict["Linear Chromaticity"] = [self._atsim.get_chromaticity('x'),
                                            self._atsim.get_chromaticity('y')]
        data_dict["Horizontal Emittance"] = self._atsim.get_horizontal_emittance() * 1e12
        data_dict["Linear Dispersion Action"] = self._atsim.get_linear_dispersion_action()
        data_dict["Momentum Spread"] = self._atsim.get_energy_spread()
        data_dict["Linear Momentum Compaction"] = self._atsim.get_momentum_compaction()
        data_dict["Energy Loss per Turn"] = self._atsim.get_energy_loss()
        data_dict["Damping Times"] = self._atsim.get_damping_times() * 1e3
        data_dict["Damping Partition Numbers"] = self._atsim.get_damping_partition_numbers()
        return data_dict

    def get_element_data(self, selected_s_pos):
        """Calculate the local (for the element at the selected s position)
        linear optics data for the lattice, and return it in a dictionary by
        its field names.
        """
        self._atsim.wait_for_calculations()
        data_dict = OrderedDict()
        all_s = self._atsim.get_s()
        index = int(numpy.where([s <= selected_s_pos for s in all_s])[0][-1])
        data_dict["Selected S Position"] = selected_s_pos
        data_dict["Element Index"] = index + 1
        data_dict["Element Start S Position"] = all_s[index]
        data_dict["Element Length"] = self._atsim.get_at_element(index+1).Length
        data_dict["Horizontal Linear Dispersion"] = self._atsim.get_dispersion()[index, 0]
        data_dict["Beta Function"] = self._atsim.get_beta()[index]
        data_dict["Derivative of Beta Function"] = self._atsim.get_alpha()[index]
        data_dict["Normalized Phase Advance"] = self._atsim.get_mu()[index]/(2*numpy.pi)
        return data_dict

    def stringify(self, value):
        """Convert numerical data into a string that can be displayed.
        """
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
        """Iterate over the global linear optics data and update the values of
        each field. Usually called after a change has been made to the lattice.
        """
        for field, value in self.get_lattice_data().items():
            self.lattice_data_widgets[field].setText(self.stringify(value))

    def update_element_data(self, s_pos):
        """Iterate over the local linear optics data and update the values of
        each field. Usually called when a new s position selection is made.
        """
        for field, value in self.get_element_data(s_pos).items():
            self.element_data_widgets[field].setText(self.stringify(value))

    def plot(self):
        """Plot the graph inside the figure.
        """
        self.figure.clear()
        self.axl = self.figure.add_subplot(111, xmargin=0, ymargin=0.025)
        self.axl.set_xlabel('s position [m]')
        self.axr = self.axl.twinx()
        self.axr.margins(0, 0.025)
        self.lattice.radiation_off()  # ensure radiation state for linopt call
        at.plot.plot_beta(self.lattice, axes=(self.axl, self.axr))
        self.canvas.draw()

    def graph_onclick(self, event):
        """Left click to make an s position selection and display a black
        dashed line at that position on the graph.
        Right click to clear a selection.
        """
        if event.xdata is not None:
            if self.s_selection is not None:
                self.s_selection.remove()  # remove old s selection line
            if event.button == 1:
                self.s_selection = self.axl.axvline(event.xdata, color="black",
                                                    linestyle='--', zorder=3)
                self.update_element_data(event.xdata)
            else:  # if not right click clear selection data
                self.s_selection = None
                for lab in self.element_data_widgets.values():
                    lab.setText("N/A")
            self.canvas.draw()

    def resize_graph(self, width, height, redraw=False):
        """Resize the graph to a new width and(or) height; can also be used to
        force a redraw of the graph, without resizing, by way of the redraw
        argument.
        """
        if not redraw:  # doesn't redraw if not necessary and not forced
            redraw = bool((int(width) != int(self.graph_width)) or
                          (int(height) != int(self.graph_height)))
        if redraw:
            self.canvas.flush_events()
            self.canvas.setMaximumWidth(int(width))
            self.canvas.setMaximumHeight(int(height))
            self.canvas.resize(int(width), int(height))
            self.graph_width = int(width)
            self.graph_height = int(height)

    def refresh_all(self):
        """Refresh the graph, global linear optics data, and local linear
        optics data.
        """
        self.plot()
        self.resizeEvent(None)
        self.update_lattice_data()
        s_pos = self.element_data_widgets["Selected S Position"].text()
        if s_pos != "N/A":
            self.update_element_data(float(s_pos))
            self.s_selection.remove()
            self.s_selection = self.axl.axvline(float(s_pos), color="black",
                                                linestyle='--', zorder=3)
            self.canvas.draw()
        for box in self.edit_boxes:
            box.refresh()

    def resizeEvent(self, event):
        """Called when the window is resized; resizes the graph and lattice
        representation accordingly for the new window size.
        N.B.
            1) The hard-coded pixel offsets are almost entirely arbitrary and
               "just work^TM" for me, but may need to be changed for alignment
               to work properly on a different machine.
            2) All resizing related code is held together by willpower and
               voodoo magic and will break if it senses fear.
        """
        # Determine graph width from window size
        width = int(max([self.frameGeometry().width() - 500, 1000]))
        height = int(max([self.frameGeometry().height() - 350, 480]))
        # Resize graph
        self.resize_graph(width, height)
        # Get non-zero length element representation widths from graph width
        widths = self.calc_new_width(width - 125)
        for el_repr, w in zip(self.lat_repr, widths):
            if w != el_repr.width:
                el_repr.changeSize(w)
        # Two px more to account for end bars
        self.mid_line.changeSize(width - 123)
        # Get lattice representation width from graph width
        zlr = self.calc_zero_len_repr(width - 125)
        zl_widths = [el_repr.width for el_repr in zlr]
        for el_repr, w in zip(self.zl_repr, zl_widths):
            el_repr.changeSize(w)
        # If not a refresh call then resize the window
        if event is not None:
            super().resizeEvent(event)


class element_repr(QWidget):
    """Class for creating the coloured element representation bars/boxes.
    """
    def __init__(self, index, colour, width, height=50, drag=True):
        # Default height is 50px making the total height, including the
        # dividing line, of the lattice representation 101px.
        # Other values don't work.
        super().__init__()
        self.index = index
        self.colour = colour
        self.width = width
        self.height = height
        self.draggable = drag
        self.setMinimumHeight(height)
        self.setMinimumWidth(width)

    def paintEvent(self, event):
        """Called on creation and resize(repaint).
        """
        qp = QPainter(self)
        qp.setPen(self.colour)
        qp.setBrush(self.colour)
        qp.drawRect(0, 0, self.width, self.height)

    def changeSize(self, width, height=None):
        """Called on resize; minimum width and height are set to prevent
        stretching/squishing.
        """
        # Allowing height changing here is a recipe for disaster...
        self.width = width
        self.setMinimumWidth(width)
        if height is not None:
            self.height = height
            self.setMinimumHeight(height)
        self.repaint()

    def mouseMoveEvent(self, event):
        """Allows drag and drop functionality, on left click and hold.
        """
        if self.draggable:
            if event.buttons() == Qt.LeftButton:
                mimeData = QMimeData()
                mimeData.setText(str(self.index))
                drag = QDrag(self)
                drag.setMimeData(mimeData)
                drag.exec(Qt.MoveAction)
        return


class edit_box(QGroupBox):
    """Class for creating element editing boxes that element representations
    can be dragged to to display information and be edited.
    """
    def __init__(self, window, atsim):
        super().__init__()
        self.parent_window = window
        self.lattice = atip.utils.get_sim_lattice(atsim)
        self._atsim = atsim
        self.setMaximumSize(350, 200)
        self.setAcceptDrops(True)
        self.dl = self.create_box()

    def create_box(self):
        """Create the field labels and input/display for a box.
        """
        data_labels = {}
        grid = QGridLayout()
        float_validator = QDoubleValidator()
        float_validator.setNotation(QDoubleValidator.StandardNotation)
        pass_validator = PassMethodValidator()
        index = QLabel("Index")
        index.setStyleSheet("background-color:none;")
        grid.addWidget(index, 0, 0)
        data_labels["Index"] = QLabel("N/A")
        data_labels["Index"].setStyleSheet("background-color:none;")
        grid.addWidget(data_labels["Index"], 0, 1)
        type_ = QLabel("Type")
        type_.setStyleSheet("background-color:none;")
        grid.addWidget(type_, 1, 0)
        data_labels["Type"] = QLabel("N/A")
        data_labels["Type"].setStyleSheet("background-color:none;")
        grid.addWidget(data_labels["Type"], 1, 1)
        length = QLabel("Length")
        length.setStyleSheet("background-color:none;")
        grid.addWidget(length, 2, 0)
        data_labels["Length"] = QLineEdit("N/A")
        data_labels["Length"].setAcceptDrops(False)
        data_labels["Length"].setValidator(float_validator)
        data_labels["Length"].editingFinished.connect(self.enterPress)
        grid.addWidget(data_labels["Length"], 2, 1)
        pass_meth = QLabel("PassMethod")
        pass_meth.setStyleSheet("background-color:none;")
        grid.addWidget(pass_meth, 3, 0)
        data_labels["PassMethod"] = QLineEdit("N/A")
        data_labels["PassMethod"].setAcceptDrops(False)
        data_labels["PassMethod"].setValidator(pass_validator)
        data_labels["PassMethod"].editingFinished.connect(self.enterPress)
        grid.addWidget(data_labels["PassMethod"], 3, 1)
        data_labels["SetPoint"] = (QComboBox(), QLineEdit("N/A"))
        data_labels["SetPoint"][0].currentIndexChanged.connect(self.change_list_item)
        data_labels["SetPoint"][0].setSizeAdjustPolicy(0)
        data_labels["SetPoint"][0].addItem("Set Point")
        grid.addWidget(data_labels["SetPoint"][0], 5, 0)
        data_labels["SetPoint"][1].setAcceptDrops(False)
        data_labels["SetPoint"][1].setValidator(float_validator)
        data_labels["SetPoint"][1].editingFinished.connect(self.enterPress)
        grid.addWidget(data_labels["SetPoint"][1], 5, 1)
        self.setLayout(grid)
        return data_labels

    def dragEnterEvent(self, event):
        """Receive the mime data of a dragged object, only accept if the
        element index is a positive integer.
        """
        if event.mimeData().text().isdigit():
            event.accept()
        else:  # Reject all but positive integers.
            event.ignore()

    def dropEvent(self, event):
        """Accept all dropped objects as dragEnterEvent will already have
        rejected all undesirables. On drop action update the edit box to
        display the appropriate data for that element.
        """
        element = self.lattice[int(event.mimeData().text()) - 1]
        self.dl["Index"].setText(event.mimeData().text())
        self.dl["Type"].setText(element.Class)
        self.dl["Length"].setText(str(round(element.Length, 5)))
        self.dl["PassMethod"].setText(element.PassMethod)
        # Clear ComboBox (drop-down list) contents.
        for i in range(self.dl["SetPoint"][0].count()):
            self.dl["SetPoint"][0].removeItem(i)
        # Determine correct set point field based on element type.
        if isinstance(element, at.elements.Bend):
            self.dl["SetPoint"][0].addItem("BendingAngle")
            self.dl["SetPoint"][1].setText(str(round(element.BendingAngle, 5)))
        elif isinstance(element, at.elements.Corrector):
            if (element.FamName == 'HSTR') or (element.FamName == 'HTRIM'):
                self.dl["SetPoint"][0].addItem("X Kick")
                self.dl["SetPoint"][1].setText(str(round(element.KickAngle[0],
                                                         5)))
            elif (element.FamName == 'VSTR') or (element.FamName == 'VTRIM'):
                self.dl["SetPoint"][0].addItem("Y Kick")
                self.dl["SetPoint"][1].setText(str(round(element.KickAngle[1],
                                                         5)))
            else:
                self.dl["SetPoint"][0].addItems(["X Kick", "Y Kick"])
        elif isinstance(element, at.elements.Sextupole):
            self.dl["SetPoint"][0].addItem("H")
            self.dl["SetPoint"][1].setText(str(round(element.H, 5)))
        elif isinstance(element, at.elements.Quadrupole):
            self.dl["SetPoint"][0].addItem("K")
            self.dl["SetPoint"][1].setText(str(round(element.K, 5)))
        elif isinstance(element, at.elements.RFCavity):
            self.dl["SetPoint"][0].addItems(["Frequency", "Voltage",
                                             "HarmNumber", "Energy"])
            self.dl["SetPoint"][1].setText(str(round(element.Frequency, 5)))
        else:  # Drift or unsupported type.
            self.dl["SetPoint"][0].addItem("Set Point")
            self.dl["SetPoint"][1].setText("N/A")
        event.accept()

    def enterPress(self):
        """On an enter press in an editable field, do some data processing and
        then apply the change to the base lattice, then trigger a recalculation
        of the linear optics data, then refresh the window to display the newly
        calculated data.
        """
        change = True
        element = self.lattice[int(self.dl["Index"].text()) - 1]
        if round(element.Length, 5) != float(self.dl["Length"].text()):
            length = float(self.dl["Length"].text())
            element.Length = length
        elif element.PassMethod != self.dl["PassMethod"].text():
            element.PassMethod = self.dl["PassMethod"].text()
        elif self.dl["SetPoint"][0].currentText() == "BendingAngle":
            if round(element.BendingAngle,
                     5) != float(self.dl["SetPoint"][1].text()):
                element.BendingAngle = float(self.dl["SetPoint"][1].text())
            else:
                change = False
        elif self.dl["SetPoint"][0].currentText() == "X Kick":
            if round(element.KickAngle[0],
                     5) != float(self.dl["SetPoint"][1].text()):
                element.KickAngle[0] = float(self.dl["SetPoint"][1].text())
            else:
                change = False
        elif self.dl["SetPoint"][0].currentText() == "Y Kick":
            if round(element.KickAngle[1],
                     5) != float(self.dl["SetPoint"][1].text()):
                element.KickAngle[1] = float(self.dl["SetPoint"][1].text())
            else:
                change = False
        elif self.dl["SetPoint"][0].currentText() == "H":
            if round(element.H, 5) != float(self.dl["SetPoint"][1].text()):
                element.H = float(self.dl["SetPoint"][1].text())
            else:
                change = False
        elif self.dl["SetPoint"][0].currentText() == "K":
            if round(element.K, 5) != float(self.dl["SetPoint"][1].text()):
                element.K = float(self.dl["SetPoint"][1].text())
            else:
                change = False
        elif self.dl["SetPoint"][0].currentText() == "Frequency":
            if round(element.Frequency,
                     5) != float(self.dl["SetPoint"][1].text()):
                element.Frequency = float(self.dl["SetPoint"].text())
            else:
                change = False
        elif self.dl["SetPoint"][0].currentText() == "Voltage":
            if round(element.Voltage,
                     5) != float(self.dl["SetPoint"][1].text()):
                element.Voltage = float(self.dl["SetPoint"].text())
            else:
                change = False
        elif self.dl["SetPoint"][0].currentText() == "HarmNumber":
            if round(element.HarmNumber,
                     5) != float(self.dl["SetPoint"][1].text()):
                element.HarmNumber = float(self.dl["SetPoint"].text())
            else:
                change = False
        elif self.dl["SetPoint"][0].currentText() == "Energy":
            if round(element.Energy,
                     5) != float(self.dl["SetPoint"][1].text()):
                element.Energy = float(self.dl["SetPoint"].text())
            else:
                change = False
        else:
            change = False
        if change:
            atip.utils.trigger_calc(self._atsim)
            self._atsim.wait_for_calculations()
            self.parent_window.refresh_all()

    def change_list_item(self):
        """Update the displayed data for the new field selection.
        """
        if not hasattr(self, "dl"):
            return
        element = self.lattice[int(self.dl["Index"].text()) - 1]
        if self.dl["SetPoint"][0].currentText() == "BendingAngle":
            self.dl["SetPoint"][1].setText(str(round(element.BendingAngle, 5)))
        elif self.dl["SetPoint"][0].currentText() == "X Kick":
            self.dl["SetPoint"][1].setText(str(round(element.KickAngle[0], 5)))
        elif self.dl["SetPoint"][0].currentText() == "Y Kick":
            self.dl["SetPoint"][1].setText(str(round(element.KickAngle[1], 5)))
        elif self.dl["SetPoint"][0].currentText() == "H":
            self.dl["SetPoint"][1].setText(str(round(element.H, 5)))
        elif self.dl["SetPoint"][0].currentText() == "K":
            self.dl["SetPoint"][1].setText(str(round(element.K, 5)))
        elif self.dl["SetPoint"][0].currentText() == "Frequency":
            self.dl["SetPoint"][1].setText(str(round(element.Frequency, 5)))
        elif self.dl["SetPoint"][0].currentText() == "Voltage":
            self.dl["SetPoint"][1].setText(str(round(element.Voltage, 5)))
        elif self.dl["SetPoint"][0].currentText() == "HarmNumber":
            self.dl["SetPoint"][1].setText(str(round(element.HarmNumber, 5)))
        elif self.dl["SetPoint"][0].currentText() == "Energy":
            self.dl["SetPoint"][1].setText(str(round(element.Energy, 5)))
        elif self.dl["SetPoint"][0].currentText() == "Set Point":
            self.dl["SetPoint"][1].setText("N/A")
        elif self.dl["SetPoint"][0].currentText() == "":
            return  # For some reason this happens initially, so ignore it.
        else:
            raise("Unsupported AT field type {0}."
                  .format(self.dl["SetPoint"][0].currentText()))

    def refresh(self):
        """Refresh the displayed data.
        """
        index = self.dl["Index"].text()
        if index != "N/A":
            class evnt(QEvent):
                def mimeData(self):
                    md = QMimeData()
                    md.setText(str(index))
                    return md
            self.dropEvent(evnt(63))  # Type 63 for drag and drop completion.


class PassMethodValidator(QValidator):
    """Check that a given PassMethod is valid. Used to validate inputs to the
    PassMethod fields of the edit boxes.
    """
    def __init__(self):
        super().__init__()

    def validate(self, string, pos):
        """Check that it is a  alphanumeric string of non-zero length, ending
        in 'Pass' which has a corresponding built file (e.g. DriftPass.so).
        """
        if (string != '') and (not string.isalnum()):
            return (QValidator.Invalid, string, pos)
        elif string.endswith("Pass"):
            file_name = at.load.utils.get_pass_method_file_name(string)
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
