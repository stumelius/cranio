"""
.. todo:: To be documented.
"""
import logging
import pyqtgraph as pg
import pandas as pd
from typing import Tuple, List, Iterable
from functools import partial
from PyQt5 import QtCore
from PyQt5.QtWidgets import QLineEdit, QInputDialog, QComboBox, QTableWidget, QTableWidgetItem, QAbstractItemView, \
    QLayout, QWidget, QWidgetItem, QSpacerItem, QLabel, QVBoxLayout, QPushButton, QHBoxLayout, QDoubleSpinBox, \
    QGroupBox, QMessageBox, QSpinBox, QGridLayout, QCheckBox
from sqlalchemy.exc import IntegrityError
from cranio.database import AnnotatedEvent, DISTRACTION_EVENT_TYPE_OBJECT, Document, session_scope, Patient
from cranio.core import utc_datetime

# plot style settings
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

# custom color palette for plots
color_palette = [(76, 114, 176), (85, 168, 104), (196, 78, 82),
                 (129, 114, 178), (204, 185, 116), (100, 181, 205)]

PATIENT_ID_TOOLTIP = ('Enter patient identifier.\n'
                      'NOTE: Do not enter personal information, such as names.')
SESSION_ID_TOOLTIP = ('This is a random-generated unique identifier.\n'
                      'NOTE: Value cannot be changed by the user.')
DISTRACTOR_ID_TOOLTIP = 'Enter distractor identifier/number.'


def remove_widget_from_layout(layout: QLayout, widget: QWidget):
    """
    Remove widget from a layout.

    :param layout:
    :param widget:
    :return:
    """
    layout.removeWidget(widget)
    widget.deleteLater()


def clear_layout(layout: QLayout):
    """
    Clear a layout.

    :param layout:
    :return:
    """
    for i in reversed(range(layout.count())):
        item = layout.itemAt(i)

        if isinstance(item, QWidgetItem):
            item.widget().close()
        elif isinstance(item, QSpacerItem):
            pass
        else:
            clear_layout(item.layout())
        # remove item from layout
        layout.removeItem(item)


class EditWidget(QWidget):
    """ Line edit and label widgets in a horizontal layout. """
    _edit_widget_cls = QLineEdit

    def __init__(self, label, value=None, parent=None):
        super().__init__(parent)
        self.label = QLabel(label)
        self.edit_widget = self._edit_widget_cls()
        self.layout = QHBoxLayout()
        if value is not None:
            self.value = value
        self.init_ui()

    def init_ui(self):
        """ Initialize UI elements. """
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.edit_widget)
        self.setLayout(self.layout)

    @property
    def value(self):
        """ Line edit value property. """
        return self.edit_widget.text()

    @value.setter
    def value(self, value):
        self.edit_widget.setText(value)

    @property
    def tooltip(self):
        """ Line edit tooltip property. """
        return self.edit_widget.toolTip()

    @tooltip.setter
    def tooltip(self, text):
        self.edit_widget.setToolTip(text)


class ComboEditWidget(EditWidget):
    """ EditWidget variant with a popup list instead of a line edit. """
    _edit_widget_cls = QComboBox

    def add_item(self, text: str):
        """
        Add item to the popup list.

        :param text:
        :return:
        """
        self.edit_widget.addItem(text)

    def set_item(self, index: int, text: str):
        """
        Set popup list item at specified index.

        :param index:
        :param text:
        :return:
        """
        self.edit_widget.setItemText(index, text)

    def clear(self):
        """
        Clear popup list.

        :return:
        """
        self.edit_widget.clear()

    def count(self) -> int:
        """
        Return number of items in the popup list.

        :return:
        """
        return self.edit_widget.count()

    def item_at(self, index: int):
        """
        Return popup list item at specified index.

        :param index:
        :return:
        """
        return self.edit_widget.itemText(index)

    @property
    def value(self):
        """ Popup list selected value property. """
        return self.edit_widget.currentText()

    @value.setter
    def value(self, value):
        self.edit_widget.setEditText(value)


class SpinEditWidget(EditWidget):
    """ EditWidget variant with a spin box instead of a line edit. """
    _edit_widget_cls = QSpinBox

    @property
    def value(self):
        """ Spin box value property. """
        return self.edit_widget.value()

    @value.setter
    def value(self, value):
        self.edit_widget.setValue(value)

    def step_up(self):
        """
        Increase spin box value by one step.

        :return:
        """
        self.edit_widget.stepUp()

    def step_down(self):
        """
        Decrease spin box value by one step.

        :return:
        """
        self.edit_widget.stepDown()

    def set_range(self, min: int, max: int):
        """
        Set allowed minimum and maximum values for the spin box.

        :param min:
        :param max:
        :return:
        """
        self.edit_widget.setRange(min, max)


class MetaDataWidget(QGroupBox):
    """ Widget for editing distraction session -related meta data. """
    closing = QtCore.pyqtSignal()

    def __init__(self, document: Document, parent=None):
        super().__init__(parent=parent)
        self.document = document
        self.patient_widget = ComboEditWidget('Patient', parent=self)
        self.distractor_widget = SpinEditWidget('Distractor', parent=self)
        self.toggle_patient_lock_button = QPushButton('Toggle Patient Lock')
        self.layout = QVBoxLayout()
        self.enabled = True
        self.init_ui()

    def init_ui(self):
        """
        Initialize UI elements.

        :return:
        """
        # initialize distractor as 1 and set range between 1 and 10
        self.distractor_widget.set_range(1, 10)
        self.active_distractor = 1
        self.toggle_patient_lock_button.clicked.connect(self.toggle_lock_button_clicked)
        self.layout.addWidget(self.patient_widget)
        self.layout.addWidget(self.distractor_widget)
        self.layout.addWidget(self.toggle_patient_lock_button)
        self.setLayout(self.layout)
        self.setTitle('Session information')
        # set tooltips
        self.patient_widget.tooltip = PATIENT_ID_TOOLTIP
        self.distractor_widget.tooltip = DISTRACTOR_ID_TOOLTIP

    def add_patient(self, text: str):
        """
        Add patient to popup list.

        :param text:
        :return:
        """
        self.patient_widget.add_item(text)

    def update_patients_from_database(self):
        """
        Clear and populate patient popup list from database.

        :return:
        """
        logging.debug('Update patients called')
        self.patient_widget.clear()
        with session_scope() as s:
            for p in s.query(Patient).all():
                # populate patient widget
                logging.debug(f'patient_id = {p.patient_id}')
                self.patient_widget.add_item(p.patient_id)

    def patients(self) -> List[str]:
        """

        :return: List of patient identifiers
        """
        return [self.patient_widget.item_at(i) for i in range(self.patient_widget.count())]

    @property
    def active_patient(self) -> str:
        """ Active patient in the popup list. """
        return self.patient_widget.value

    @active_patient.setter
    def active_patient(self, patient_id: str):
        self.patient_widget.value = patient_id
        self.document.patient_id = patient_id

    @property
    def active_distractor(self) -> int:
        return self.distractor_widget.value

    @active_distractor.setter
    def active_distractor(self, distractor_id: int):
        self.distractor_widget.value = distractor_id
        self.document.distractor_id = distractor_id

    def lock_patient(self, lock: bool):
        """
        Lock patient edit widget.

        :param lock:
        :return:
        """
        self.enabled = not lock
        self.patient_widget.setEnabled(self.enabled)
        logging.debug(f'Patient lock = {lock}')

    def toggle_lock_button_clicked(self):
        """
        Toggle patient widget lock.

        :return:
        """
        self.lock_patient(self.enabled)


def add_patient(patient_id: str) -> Patient:
    """
    Add new patient to the database.

    :param patient_id: Patient identifier
    :return:
    :raises sqlalchemy.exc.IntegrityError: if the patient already exists.
    """
    patient = Patient(patient_id=patient_id)
    with session_scope() as session:
        session.add(patient)
    return patient


def prompt_create_patient(parent_widget) -> str:
    """
    Prompt the user to create a new patient id.
    The patient is inserted to the database if the patient does not already exist.

    :param parent_widget:
    :return: Patient identifier or None if no patient was created (user cancelled or patient already exists)
    """
    # open create patient dialog
    patient_id, ok = QInputDialog.getText(parent_widget, 'Create patient', 'Enter patient id:')
    if not ok:
        return
    # try to insert patient to database
    try:
        add_patient(patient_id)
        return patient_id
    except IntegrityError:
        QMessageBox.information(parent_widget, 'Invalid value',
                                f'Patient id "{patient_id}" is invalid or already exists in the database')


class PatientWidget(QWidget):
    """
    View existing patients and add new ones to the database
    """

    def __init__(self):
        super().__init__()
        self.main_layout = QVBoxLayout()
        self.label = QLabel('Patients')
        self.table_widget = QTableWidget(parent=self)
        self.table_widget.setColumnCount(2)
        # disable editing
        self.table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # column headers from Patient table
        self.table_widget.setHorizontalHeaderLabels(Patient.__table__.columns.keys())
        self.table_widget.horizontalHeader().setStretchLastSection(True);
        self.table_widget.resizeColumnsToContents()
        self.add_button = QPushButton('Add', parent=self)
        self.add_button.clicked.connect(self.add_button_clicked)
        self.main_layout.addWidget(self.label)
        self.main_layout.addWidget(self.table_widget)
        self.main_layout.addWidget(self.add_button)
        self.setLayout(self.main_layout)
        self.update_patients()

    def update_patients(self):
        """
        Update patient list.

        :return:
        """
        with session_scope() as session:
            for i, patient in enumerate(session.query(Patient).all()):
                self.table_widget.setRowCount(i + 1)
                self.table_widget.setItem(i, 0, QTableWidgetItem(patient.patient_id))
                self.table_widget.setItem(i, 1, QTableWidgetItem(str(patient.created_at)))

    def add_patient(self, patient_id: str):
        """
        Add patient to the database and update patient list.

        :param patient_id:
        :return:
        """
        add_patient(patient_id)
        self.update_patients()

    def add_button_clicked(self):
        """
        Prompt user to insert new patient identifier and update patient list.

        :return:
        """
        prompt_create_patient(self)
        self.update_patients()

    def patient_count(self) -> int:
        """
        Return number of patients in the list.

        :return:
        """
        return self.table_widget.rowCount()


class MeasurementWidget(QWidget):
    """ Multiplot widget and buttons to start and stop data recording. Ok button to continue. """
    started = QtCore.pyqtSignal()
    stopped = QtCore.pyqtSignal()

    def __init__(self, producer_process=None, parent=None, document: Document=None):
        from cranio.app.window import RegionPlotWindow
        super().__init__(parent)
        self.producer_process = producer_process
        self.document = document
        self.region_plot_window = RegionPlotWindow(document=self.document, parent=self)
        self.main_layout = QVBoxLayout()
        self.plot_layout = QHBoxLayout()
        self.start_stop_layout = QVBoxLayout()
        self.multiplot_widget = VMultiPlotWidget()
        self.ok_button = QPushButton('Ok')
        self.start_button = QPushButton('Start')
        self.stop_button = QPushButton('Stop')
        self.update_timer = QtCore.QTimer()
        self.update_interval = 0.05  # seconds
        self.init_ui()

    def init_ui(self):
        """
        Initialize UI elements.

        :return:
        """
        self.plot_layout.addWidget(self.multiplot_widget)
        self.plot_layout.addLayout(self.start_stop_layout)
        self.start_stop_layout.addWidget(self.start_button)
        self.start_stop_layout.addWidget(self.stop_button)
        self.main_layout.addLayout(self.plot_layout)
        self.main_layout.addWidget(self.ok_button)
        self.setLayout(self.main_layout)
        # connect signals
        self.ok_button.clicked.connect(self.ok_button_clicked)
        self.start_button.clicked.connect(self.start_button_clicked)
        self.stop_button.clicked.connect(self.stop_button_clicked)
        self.update_timer.timeout.connect(self.update)

    def plot(self, df: pd.DataFrame):
        """
        Plot a dataframe in the multiplot widget.

        :param df:
        :return:
        """
        self.multiplot_widget.plot(df)

    def add_plot(self, label: str):
        """
        Add a plot to the multiplot widget.

        :param label: Plot label
        :return:
        """
        return self.multiplot_widget.add_plot_widget(label)

    def get_plot(self, label: str):
        """
        Return plot widget by label.

        :param label:
        :return:
        """
        return self.multiplot_widget.find_plot_widget_by_label(label)

    def update(self):
        """
        Read data from the producer process and append to the plot.

        :return:
        """
        self.producer_process.store.read()
        self.producer_process.store.flush()
        data = self.producer_process.read()
        self.plot(data)

    @QtCore.pyqtSlot()
    def ok_button_clicked(self):
        """
        Start the event detection sequence after "Stop" is clicked.

        :return:
        """
        if len(self.multiplot_widget.plot_widgets) > 1:
            raise NotImplementedError('No support for over 2-dimensional data')
        for p in self.multiplot_widget.plot_widgets:
            # copy plot widget
            p_new = self.region_plot_window.plot(x=p.x, y=p.y)
            p_new.y_label = p.y_label
        return self.region_plot_window.exec_()

    def start_button_clicked(self):
        """
        Start the producer process, disable "Ok" button and emit `started` signal.
        If producer process is None, an error box is shown.

        :return:
        """
        if self.producer_process is None:
            QMessageBox.critical(self, 'Error', 'No producer process defined')
            return
        self.update_timer.start(self.update_interval * 1000)
        self.document.started_at = utc_datetime()
        self.producer_process.start()
        self.started.emit()
        self.ok_button.setEnabled(False)

    def stop_button_clicked(self):
        """
        Stop the producer process, enable "Ok" button and emit `stopped` signal.
        If producer process is None, nothing happens.

        :return:
        """
        if self.producer_process is None:
            return
        self.producer_process.pause()
        self.update_timer.stop()
        self.stopped.emit()
        self.ok_button.setEnabled(True)


class PlotWidget(pg.PlotWidget):
    """ Widget for displaying a (real-time) plot """

    # default plot configuration
    plot_configuration = {'antialias': True, 'pen': pg.mkPen(color_palette[0])}

    def __init__(self, parent=None):
        super(PlotWidget, self).__init__(parent)
        self.x = []
        self.y = []
        self.init_ui()

    def init_ui(self):
        """ Initialize UI elements. """
        self.showGrid(True, True, 0.1)
        self.enable_interaction(False)

    @property
    def x_label(self):
        """ Plot x label property. """
        return self.getAxis('bottom').labelText

    @x_label.setter
    def x_label(self, value):
        if value is None:
            value = ''
        self.setLabel('bottom', value)

    @property
    def y_label(self):
        """ Plot y label property. """
        return self.getAxis('left').labelText

    @y_label.setter
    def y_label(self, value):
        if value is None:
            value = ''
        self.setLabel('left', value)

    def enable_interaction(self, enable: bool):
        """
        Enable/disable interaction.

        :param enable:
        :return:
        """
        self.setMouseEnabled(enable, enable)
        self.setMenuEnabled(enable)

    def clear_plot(self):
        """
        Clear the plot.

        :return:
        """
        self.x = []
        self.y = []
        return self.getPlotItem().clear()

    def plot(self, x: Iterable[float], y: Iterable[float], mode: str = 'o'):
        """
        Plot (x, y) data.

        :param x:
        :param y:
        :param mode: Plot mode ('o' = overwrite, 'a' = append)
        :return:
        :raises ValueError: if invalid plot mode argument
        """
        if mode == 'o':
            self.x = list(x)
            self.y = list(y)
        elif mode == 'a':
            self.x += list(x)
            self.y += list(y)
        else:
            raise ValueError('Invalid mode {}'.format(mode))
        self.getPlotItem().plot(self.x, self.y, clear=True, **self.plot_configuration)
        return self


class RegionEditWidget(QGroupBox):
    """ Widget for editing a LinearRegionItem and editing event meta data. """

    def __init__(self, parent: pg.LinearRegionItem, event_number: int, document: Document):
        """

        :param parent:
        :param event_number:
        :param document: Data parent document
        """
        super(RegionEditWidget, self).__init__()
        self.parent = parent
        self.event_number = event_number
        self.document = document
        # layouts
        self.main_layout = QVBoxLayout()
        self.done_layout = QHBoxLayout()
        self.boundary_layout = QHBoxLayout()
        # widgets
        self.done_label = QLabel('Done')
        self.done_checkbox = QCheckBox()
        self.minimum_edit = QDoubleSpinBox()
        self.maximum_edit = QDoubleSpinBox()
        self.remove_button = QPushButton('Remove')
        self.init_ui()

    def init_ui(self):
        """ Initialize UI elements. """
        self.setTitle('Region')
        self.setLayout(self.main_layout)
        self.done_layout.addWidget(self.done_label)
        self.done_layout.addWidget(self.done_checkbox)
        self.boundary_layout.addWidget(self.minimum_edit)
        self.boundary_layout.addWidget(self.maximum_edit)
        self.main_layout.addLayout(self.done_layout)
        self.main_layout.addLayout(self.boundary_layout)
        self.main_layout.addWidget(self.remove_button)
        self.minimum_edit.setSingleStep(0.01)
        self.maximum_edit.setSingleStep(0.01)
        # FIXME: region.bounds is always (0,0)
        # self.minimum_edit.setRange(self.region.bounds.left(), self.region.bounds.right())
        self.minimum_edit.setValue(self.region()[0])
        self.maximum_edit.setValue(self.region()[1])

        # connect signals
        self.minimum_edit.valueChanged.connect(partial(self.value_changed, self.minimum_edit))
        self.maximum_edit.valueChanged.connect(partial(self.value_changed, self.maximum_edit))
        self.parent.sigRegionChanged.connect(self.region_changed)
        # responsibility for connecting the remove button lies in the RegionWidget

    def is_done(self) -> bool:
        """
        Return boolean indicating if the done checkbox state is Checked.

        :return:
        """
        return self.done_checkbox.checkState() == QtCore.Qt.Checked

    def set_done(self, state: bool):
        """
        Set done check box state as Checked (True) or Unchecked (False).

        :param state:
        :return:
        """
        state_map = {True: QtCore.Qt.Checked, False: QtCore.Qt.Unchecked}
        self.done_checkbox.setCheckState(state_map[state])

    def region(self) -> Tuple[float, float]:
        """
        Return region edges.

        :return:
        """
        return self.parent.getRegion()

    def left_edge(self) -> float:
        """
        Return left edge of the region.

        :return:
        """
        return self.region()[0]

    def right_edge(self) -> float:
        """
        Return right edge of the region.

        :return:
        """
        return self.region()[1]

    def get_annotated_event(self) -> AnnotatedEvent:
        """
        Create an AnnotatedEvent table row from the edit widget data.

        :return:
        """
        # only distraction events are supported
        return AnnotatedEvent(event_type=DISTRACTION_EVENT_TYPE_OBJECT.event_type,
                              event_num=self.event_number, document_id=self.document.document_id,
                              event_begin=self.left_edge(), event_end=self.right_edge(), annotation_done=self.is_done())

    def set_region(self, edges: Tuple[float, float]):
        """
        Set region edges.

        :param edges:
        :return:
        """
        self.parent.setRegion(edges)

    def set_bounds(self, bounds: Tuple[float, float]):
        """
        Set region bounds.

        :param bounds:
        :return:
        """
        self.parent.setBounds(bounds)

    def value_changed(self, widget: QDoubleSpinBox, value: float):
        """
        Update region edges.

        :param widget:
        :param value:
        :return:
        :raises ValueError: if invalid widget argument
        """
        old_edges = self.region()
        if widget == self.minimum_edit:
            new_edges = (max(old_edges), value)
        elif widget == self.maximum_edit:
            new_edges = (value, min(old_edges))
        else:
            ValueError('Invalid widget')
        self.set_region(new_edges)

    def region_changed(self):
        """
        Update minimum and maximum edit widget values.

        :return:
        """
        new_edges = self.region()
        self.minimum_edit.setValue(min(new_edges))
        self.maximum_edit.setValue(max(new_edges))


class RegionPlotWidget(QWidget):
    """ Plot widget with region selection and edit functionality. """

    def __init__(self, document: Document, parent=None):
        """
        :param document: Data parent document
        :param parent:
        """
        super().__init__(parent)
        self.document = document
        self.plot_widget = PlotWidget()
        self.main_layout = QHBoxLayout()
        self.edit_layout = QVBoxLayout()
        self.add_layout = QGridLayout()
        # region items mapped as {LinearRegionItem: RegionEditWidget}
        self.region_edit_map = dict()
        self.add_count = QSpinBox()
        self.add_button = QPushButton('Add')
        self.remove_all_button = QPushButton('Remove all')
        self.init_ui()

    def init_ui(self):
        """ Initialize UI elements. """
        self.setLayout(self.main_layout)
        self.main_layout.addWidget(self.plot_widget)
        self.main_layout.addLayout(self.edit_layout)
        self.add_layout.addWidget(self.add_count, 0, 0)
        self.add_layout.addWidget(self.add_button, 0, 1)
        self.add_layout.addWidget(self.remove_all_button, 1, 0, 1, 2)
        self.edit_layout.addLayout(self.add_layout)
        self.add_button.clicked.connect(self.add_button_clicked)
        self.remove_all_button.clicked.connect(self.remove_all)

    @property
    def x(self):
        """ Plot x values property. """
        return self.plot_widget.x

    @property
    def y(self):
        """ Plot y values property. """
        return self.plot_widget.y

    def plot(self, x, y, mode='o'):
        """
        Plot (x, y) data.

        :param x:
        :param y:
        :param mode: Plot mode ('o' = overwrite, 'a' = append)
        :return:
        """
        return self.plot_widget.plot(x, y, mode)

    def region_count(self) -> int:
        """
        Return number of regions.

        :return:
        """
        return len(self.region_edit_map)

    def set_add_count(self, value: int):
        """
        Set integer value to the add count widget.

        :param value:
        :return:
        """
        self.add_count.setValue(value)

    def get_region_edit(self, index: int) -> RegionEditWidget:
        """
        Return region edit widget for region at specified index.

        :param index:
        :return:
        """
        # note: edit widgets are stored in a dict and therefore are in no specific order
        return list(self.region_edit_map.values())[index]

    def find_region_by_edit(self, edit_widget: RegionEditWidget) -> pg.LinearRegionItem:
        """
        Find a linear region item that corresponds to a specified region edit widget.

        :param edit_widget:
        :return:
        :raises ValueError: if no matching region edit widget was found
        """
        try:
            return [key for key, value in self.region_edit_map.items() if value == edit_widget][0]
        except IndexError:
            raise ValueError('No matching edit widget found')

    def add_region(self, edges: Tuple[float, float], bounds: Tuple[float, float] = None,
                   movable: bool = True) -> RegionEditWidget:
        """
        Add a region to the plot.

        :param edges: Region edges
        :param bounds: Region bounds
        :param movable:
        :return:
        """
        if bounds is None:
            bounds = [min(self.x), max(self.x)]
        alpha = 125
        color = list(color_palette[len(self.region_edit_map)]) + [alpha]
        item = pg.LinearRegionItem(edges, bounds=bounds, movable=movable, brush=pg.mkBrush(*color))
        self.plot_widget.addItem(item)
        # event numbering by insertion order
        edit_widget = RegionEditWidget(item, event_number=self.region_count() + 1, document=self.document)
        edit_widget.remove_button.clicked.connect(partial(self.remove_region, edit_widget))
        self.edit_layout.insertWidget(self.edit_layout.count() - 1, edit_widget)
        self.region_edit_map[item] = edit_widget
        return edit_widget

    def remove_region(self, edit_widget: RegionEditWidget):
        """
        Remove specified region from the plot.

        :param edit_widget:
        :return:
        """
        key = self.find_region_by_edit(edit_widget)
        self.region_edit_map.pop(key, None)
        self.plot_widget.removeItem(key)
        remove_widget_from_layout(self.edit_layout, edit_widget)

    def remove_at(self, index: int) -> RegionEditWidget:
        """
        Remove region at specified index.

        :param index:
        :return: RegionEditWidget of the removed region
        """
        edit_widget = self.get_region_edit(index)
        self.remove_region(edit_widget)
        return edit_widget

    def add_button_clicked(self):
        """
        Add a number of regions to the plot matching the number in the add spin box.
        The region edges are initialized so that the region widths are constant and the regions do not overlap.

        :return:
        """
        if len(self.x) == 0:
            logging.error('Unable to add region to empty plot')
            return 0
        count = self.add_count.value()
        if count > 0:
            x_min = min(self.x)
            interval = (max(self.x) - x_min) / count
            for i in range(count):
                # insert at uniform intervals
                low = x_min + i * interval
                high = x_min + (i + 1) * interval
                self.add_region([low, high])

    def remove_all(self):
        """
        Remove all regions from the plot.

        :return:
        """
        for edit_widget in list(self.region_edit_map.values()):
            self.remove_region(edit_widget)

    def get_annotated_events(self) -> List[AnnotatedEvent]:
        """
        Return an AnnotatedEvent for each event region in the plot.

        :return:
        """
        return [self.get_region_edit(i).get_annotated_event() for i in range(self.region_count())]


class VMultiPlotWidget(QWidget):
    """ Display multiple plots in a vertical layout. """

    def __init__(self, parent=None):
        super(VMultiPlotWidget, self).__init__(parent=parent)
        self.plot_widgets = []
        self.title_label = QLabel()
        self.main_layout = QVBoxLayout()
        self.init_ui()
        # add placeholder widget
        self.placeholder = PlotWidget()
        self.main_layout.addWidget(self.placeholder)

    def init_ui(self):
        """ Initialize UI elements. """
        self.setLayout(self.main_layout)
        self.title_label.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
        self.main_layout.addWidget(self.title_label)

    @property
    def title(self):
        """ Plot title property. """
        return self.title_label.text()

    @title.setter
    def title(self, value):
        self.title_label.setText(value)

    def find_plot_widget_by_label(self, label: str):
        """
        Find plot by its label.

        :param label: Plot label, or y-axis name
        :return:
        """
        for p in self.plot_widgets:
            if p.y_label == label:
                return p

    def add_plot_widget(self, label: str):
        """
        Add a plot.

        :param label: Plot label, or y-axis name
        :return:
        :raises ValueError: if a plot with the specified label already exists
        """
        if self.find_plot_widget_by_label(label) is not None:
            raise ValueError('A plot widget with label {} already exists'.format(label))
        # if placeholder exists, use it
        # NOTE: no need to add to layout as placeholder is there by default
        if self.placeholder is not None:
            plot_widget = self.placeholder
            self.placeholder = None
        # if no placeholder exists, create new
        else:
            plot_widget = PlotWidget()
            self.main_layout.addWidget(plot_widget)
        plot_widget.y_label = label
        self.plot_widgets.append(plot_widget)
        return plot_widget

    def plot(self, df: pd.DataFrame, title: str = '', mode: str = 'o'):
        """
        Plot a dataframe.

        :param df: Pandas DataFrame where index is the x axis.
        :param title: Plot title.
        :param mode:
        :return:
        """
        # Data is stored as a DataFrame
        # The dataframe is appended during recording
        # Ideally, the real-time plot is updated automatically once the dataframe is updated
        # Alternatively, real-time plot can be updated at regular intervals
        #
        # Example:
        # update_timer = QTimer()
        # update_timer.setInterval(100)
        # update_timer.timeout.connect(self.update)
        # def update(self):
        #     data = devices.output()
        #     self.figure_window.update(data)
        self.title = title
        # find already initialized columns
        initialized_columns = [p.y_label for p in self.plot_widgets if p.y_label in df]
        # leftover columns need to be initialized
        non_initialized_columns = filter(lambda c: c not in initialized_columns, df.columns)
        for c in non_initialized_columns:
            self.add_plot_widget(c)
        # plot each column
        for c in df:
            plot_widget = self.find_plot_widget_by_label(c)
            plot_widget.plot(x=df.index, y=df[c], mode=mode)

    def clear(self):
        """
        Clear all plots.

        :return:
        """
        for p in self.plot_widgets:
            p.clear()

    def reset(self):
        """
        Remove all plots from the layout.

        :return:
        """
        for p in self.plot_widgets:
            remove_widget_from_layout(self.main_layout, p)
        self.plot_widgets = []