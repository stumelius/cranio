"""
GUI widgets.
"""
import pyqtgraph as pg
import pandas as pd
from enum import Enum
from typing import Tuple, List, Iterable, Union
from functools import partial
from PyQt5 import QtCore
from PyQt5.QtWidgets import (
    QLineEdit,
    QInputDialog,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QAbstractItemView,
    QLayout,
    QWidget,
    QWidgetItem,
    QLabel,
    QVBoxLayout,
    QPushButton,
    QHBoxLayout,
    QDoubleSpinBox,
    QGroupBox,
    QMessageBox,
    QSpinBox,
    QGridLayout,
    QCheckBox,
)
from sqlalchemy.exc import IntegrityError
from cranio.model import (
    AnnotatedEvent,
    session_scope,
    Patient,
    EventType,
    Measurement,
    Session,
    Database,
)
from cranio.utils import logger
from cranio.producer import get_all_from_queue, datetime_to_seconds

# Plot style settings
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')
# Custom color palette for plots
color_palette = [
    (76, 114, 176),
    (85, 168, 104),
    (196, 78, 82),
    (129, 114, 178),
    (204, 185, 116),
    (100, 181, 205),
]
DISTRACTOR_ID_TOOLTIP = 'Enter distractor identifier/number.'


def filter_last_n_seconds(x_arr, n: float):
    last = x_arr[-1]
    for x in x_arr:
        yield x >= (last - n)


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
    Clear all widgets from a QLayout.

    :param layout:
    :return:
    """
    widget_count = layout.count()
    for i in reversed(range(widget_count)):
        item = layout.itemAt(i)
        if isinstance(item, QWidgetItem):
            item.widget().close()
        else:
            clear_layout(item.layout())
        # Remove item from layout
        layout.removeItem(item)


class PlotMode(Enum):
    OVERWRITE = 'o'
    APPEND = 'a'


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


class DoubleSpinEditWidget(SpinEditWidget):
    """ EditWidget variant with a spin box instead of a line edit. """

    _edit_widget_cls = QDoubleSpinBox

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.edit_widget.setSingleStep(0.1)


class CheckBoxEditWidget(EditWidget):
    """ EditWidget variant with a spin box instead of a line edit. """

    _edit_widget_cls = QCheckBox
    state_map = {True: QtCore.Qt.Checked, False: QtCore.Qt.Unchecked}

    @property
    def value(self):
        """ Check box state property. """
        return self.edit_widget.checkState() == QtCore.Qt.Checked

    @value.setter
    def value(self, state: bool):
        self.edit_widget.setCheckState(self.state_map[state])


class MetaDataWidget(QGroupBox):
    """ Widget for editing distraction session -related meta data. """

    signal_close = QtCore.pyqtSignal()

    def __init__(self, database: Database, parent=None):
        super().__init__(parent=parent)
        self.database = database
        self.patient_widget = EditWidget('Patient', parent=self)
        self.patient_widget.setEnabled(False)
        self.operator_widget = EditWidget('Operator', parent=self)
        self.layout = QVBoxLayout()
        self.enabled = True
        self.init_ui()

    def init_ui(self):
        """
        Initialize UI elements.

        :return:
        """
        self.layout.addWidget(self.patient_widget)
        self.layout.addWidget(self.operator_widget)
        self.setLayout(self.layout)
        self.setTitle('Session information')

    @property
    def patient_id(self) -> str:
        return self.patient_widget.value

    @patient_id.setter
    def patient_id(self, value: str):
        self.patient_widget.value = str(value)

    @property
    def operator(self) -> str:
        return self.operator_widget.value

    @operator.setter
    def operator(self, operator: str):
        self.operator_widget.value = str(operator)


class PatientWidget(QWidget):
    """
    View existing patients and add new ones to the database
    """

    def __init__(self, database: Database):
        super().__init__()
        self.database = database
        self.main_layout = QVBoxLayout()
        self.button_layout = QHBoxLayout()
        self.label = QLabel('Patients')
        self.select_widget = QComboBox(parent=self)
        self.add_button = QPushButton('New', parent=self)
        self.ok_button = QPushButton('OK', parent=self)
        self.main_layout.addWidget(self.label)
        self.main_layout.addWidget(self.select_widget)
        self.button_layout.addWidget(self.add_button)
        self.button_layout.addWidget(self.ok_button)
        self.main_layout.addLayout(self.button_layout)
        self.setLayout(self.main_layout)
        self.update_patients()

    def update_patients(self):
        """
        Update patient list.

        :return:
        """
        self.select_widget.clear()
        with session_scope(self.database) as session:
            for patient in session.query(Patient).all():
                self.select_widget.addItem(patient.patient_id)

    def patient_count(self) -> int:
        """
        Return number of patients in the list.

        :return:
        """
        return self.select_widget.count()

    def get_selected_patient_id(self) -> str:
        return self.select_widget.currentText()


class SessionWidget(QWidget):
    """
    View existing sessions and let user select one.
    """

    def __init__(self, database: Database):
        super().__init__()
        self.database = database
        self.main_layout = QVBoxLayout()
        self.label = QLabel('Sessions')
        self.table_widget = QTableWidget(parent=self)
        self.table_widget.setColumnCount(2)
        # Disable editing
        self.table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # Set column names
        self.table_widget.setHorizontalHeaderLabels(['session_id', 'started_at'])
        self.table_widget.horizontalHeader().setStretchLastSection(True)
        self.table_widget.resizeColumnsToContents()
        self.select_button = QPushButton('Select session')
        self.cancel_button = QPushButton('Cancel')
        # Set layout
        self.main_layout.addWidget(self.label)
        self.main_layout.addWidget(self.table_widget)
        self.main_layout.addWidget(self.select_button)
        self.main_layout.addWidget(self.cancel_button)
        self.setLayout(self.main_layout)
        self.sessions = []
        self.update_sessions()

    def update_sessions(self):
        """
        Update session list.

        :return:
        """
        # Clear current contents
        self.sessions = []
        self.table_widget.clear()
        # Add new contents
        with session_scope(self.database) as s:
            for i, session in enumerate(s.query(Session).all()):
                self.sessions.append(session)
                self.table_widget.setRowCount(i + 1)
                self.table_widget.setItem(i, 0, QTableWidgetItem(session.session_id))
                self.table_widget.setItem(
                    i, 1, QTableWidgetItem(str(session.started_at))
                )

    def session_count(self) -> int:
        """
        Return number of sessions in the list.

        :return:
        """
        return self.table_widget.rowCount()

    @property
    def session_id(self) -> str:
        """ Return session_id of active (selected) session. If no session is selected, None is returned. """
        try:
            session_id = self.table_widget.item(
                self.table_widget.currentRow(), 0
            ).text()
        except AttributeError:
            # AttributeError: 'NoneType' object has no attribute 'text'
            session_id = None
        logger.debug(f'Active session_id = {session_id}')
        return session_id

    def select_session(self, session_id: str):
        """
        Select select by session_id.

        :param session_id:
        :return:
        """
        for i in range(self.session_count()):
            item = self.table_widget.item(i, 0)
            if item.text() == session_id:
                self.table_widget.setCurrentCell(i, 0)
                break
        else:
            logger.error(f'No session {session_id} in SessionWidget')


class MeasurementWidget(QWidget):
    """ Multiplot measurement widget and buttons to start and stop data recording. Ok button to continue. """

    def __init__(self, database: Database, producer_process=None, parent=None):
        super().__init__(parent)
        self.database = database
        self.producer_process = producer_process
        self.main_layout = QVBoxLayout()
        self.plot_layout = QHBoxLayout()
        self.start_stop_layout = QVBoxLayout()
        self.multiplot_widget = VMultiPlotWidget()
        self.start_button = QPushButton('Start')
        self.distractor_widget = SpinEditWidget('Distractor', parent=self)
        self.stop_button = QPushButton('Stop')
        self.update_timer = QtCore.QTimer()
        self.update_interval = 0.05  # seconds
        self.distractor_widget.set_range(1, 10)
        self.init_ui()

    def init_ui(self):
        """
        Initialize UI elements.

        :return:
        """
        self.plot_layout.addWidget(self.multiplot_widget)
        self.plot_layout.addLayout(self.start_stop_layout)
        self.start_stop_layout.addWidget(self.start_button)
        self.start_stop_layout.addWidget(self.distractor_widget)
        self.start_stop_layout.addWidget(self.stop_button)
        self.main_layout.addLayout(self.plot_layout)
        self.setLayout(self.main_layout)
        self.distractor_widget.tooltip = DISTRACTOR_ID_TOOLTIP
        # Connect signals
        self.update_timer.timeout.connect(self.update)

    @property
    def distractor(self) -> int:
        return self.distractor_widget.value

    @distractor.setter
    def distractor(self, distractor_number: int):
        self.distractor_widget.value = distractor_number

    def plot(self, df: pd.DataFrame, mode: PlotMode = PlotMode.OVERWRITE):
        """
        Plot a dataframe in the multiplot widget.

        :param df:
        :param mode: plot mode
        :return:
        """
        self.multiplot_widget.plot(df, mode=mode)

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
        index_arr, value_dict_arr = get_all_from_queue(self.producer_process.queue)
        # No data available
        if not index_arr:
            return
        # Convert UTC+0 datetime to seconds
        time_arr = datetime_to_seconds(
            index_arr, self.producer_process.document.started_at
        )
        # Create measurements and insert to database
        measurements = []
        for time_s, value_dict in zip(time_arr, value_dict_arr):
            m = Measurement(
                time_s=time_s,
                torque_Nm=value_dict['torque (Nm)'],
                document_id=self.producer_process.document.document_id,
            )
            measurements.append(m)
        self.database.bulk_insert(measurements)
        # Convert data to DataFrame
        x, y = zip(*[(float(m.time_s), float(m.torque_Nm)) for m in measurements])
        df = pd.DataFrame({'torque (Nm)': y}, index=x)
        # Append to plot
        self.plot(df, mode=PlotMode.APPEND)

    def clear(self):
        """
        Clear the plots.

        :return:
        """
        self.multiplot_widget.clear()

    def keyPressEvent(self, event):
        # Increase active distractor when up arrow is pressed
        if event.key() == QtCore.Qt.Key_Up:
            self.distractor = self.distractor + 1
            logger.debug(
                f'Change active distractor to {self.distractor} (Up arrow pressed)'
            )
        # Decrease active distractor when down arrow is pressed
        elif event.key() == QtCore.Qt.Key_Down:
            self.distractor = self.distractor - 1
            logger.debug(
                f'Change active distractor to {self.distractor} (Down arrow pressed)'
            )
        return super().keyPressEvent(event)


class PlotWidget(pg.PlotWidget):
    """ Widget for displaying a (real-time) plot """

    # Default plot configuration
    plot_configuration = {'antialias': True, 'pen': pg.mkPen(color_palette[0])}

    def __init__(self, parent=None):
        super(PlotWidget, self).__init__(parent)
        self.x_arr = []
        self.y_arr = []
        self.init_ui()
        self.filters = []

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
        self.x_arr = []
        self.y_arr = []
        return self.getPlotItem().clear()

    def plot(
        self,
        x: Iterable[float],
        y: Iterable[float],
        mode: PlotMode = PlotMode.OVERWRITE,
    ):
        """
        Plot (x, y) data.

        :param x:
        :param y:
        :param mode:
        :return:
        :raises ValueError: if invalid plot mode argument
        """
        if mode == PlotMode.OVERWRITE:
            self.x_arr = list(x)
            self.y_arr = list(y)
        elif mode == PlotMode.APPEND:
            self.x_arr += list(x)
            self.y_arr += list(y)
        else:
            raise ValueError('Invalid mode {}'.format(mode))
        # Apply filters
        self.apply_filters()
        self.getPlotItem().plot(
            self.x_arr, self.y_arr, clear=True, **self.plot_configuration
        )
        return self

    def apply_filters(self):
        """
        Apply filters to x and y data in the order the filters were added.

        :return:
        """
        for filter_func in self.filters:
            i_arr = [i for i, x in enumerate(list(filter_func(self.x_arr))) if x]
            self.x_arr = [self.x_arr[i] for i in i_arr]
            self.y_arr = [self.y_arr[i] for i in i_arr]

    def add_filter(self, filter_func):
        """

        :param filter_func: Filter function with x values as input argument
        :return:
        """
        self.filters.append(filter_func)


class RegionEditWidget(QGroupBox):
    """ Widget for editing a LinearRegionItem and editing event meta data. """

    def __init__(self, parent: pg.LinearRegionItem, event_number: int):
        """

        :param parent:
        :param event_number:
        :param document: Data parent document
        """
        super(RegionEditWidget, self).__init__()
        self.parent = parent
        self.event_number = event_number
        # layouts
        self.main_layout = QVBoxLayout()
        self.boundary_layout = QHBoxLayout()
        # widgets
        self.done_widget = CheckBoxEditWidget('Annotation done')
        self.recorded_widget = CheckBoxEditWidget('Recorded')
        self.minimum_edit = QDoubleSpinBox()
        self.maximum_edit = QDoubleSpinBox()
        self.remove_button = QPushButton('Remove')
        self.init_ui()

    def init_ui(self):
        """ Initialize UI elements. """
        self.setTitle('Event')
        self.setLayout(self.main_layout)
        self.boundary_layout.addWidget(self.minimum_edit)
        self.boundary_layout.addWidget(self.maximum_edit)
        self.main_layout.addWidget(self.done_widget)
        self.main_layout.addWidget(self.recorded_widget)
        self.main_layout.addLayout(self.boundary_layout)
        self.main_layout.addWidget(self.remove_button)
        # Set recorded to True
        self.set_recorded(True)
        self.minimum_edit.setSingleStep(0.01)
        self.maximum_edit.setSingleStep(0.01)
        # Set range to 0 - 10000 (#109)
        self.minimum_edit.setRange(0, 10000)
        self.maximum_edit.setRange(0, 10000)
        # FIXME: region.bounds is always (0,0)
        # self.minimum_edit.setRange(self.region.bounds.left(), self.region.bounds.right())
        self.minimum_edit.setValue(self.region()[0])
        self.maximum_edit.setValue(self.region()[1])
        # connect signals
        self.minimum_edit.valueChanged.connect(
            partial(self.value_changed, self.minimum_edit)
        )
        self.maximum_edit.valueChanged.connect(
            partial(self.value_changed, self.maximum_edit)
        )
        self.parent.sigRegionChanged.connect(self.region_changed)
        # responsibility for connecting the remove button lies in the RegionWidget

    def is_done(self) -> bool:
        """
        Return boolean indicating if the done checkbox state is Checked.

        :return:
        """
        return self.done_widget.value

    def set_done(self, state: bool):
        """
        Set done check box state as Checked (True) or Unchecked (False).

        :param state:
        :return:
        """
        self.done_widget.value = state

    def is_recorded(self) -> bool:
        """
        Return boolean indicating if the recorded checkbox state is Checked.

        :return:
        """
        return self.recorded_widget.value

    def set_recorded(self, state: bool):
        """
        Set recorded check box state as Checked (True) or Unchecked (False).

        :param state:
        :return:
        """
        self.recorded_widget.value = state

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
        # NOTE: document_is is left empty (i.e,. None)
        return AnnotatedEvent(
            event_type=EventType.distraction_event_type().event_type,
            event_num=self.event_number,
            document_id=None,
            event_begin=self.left_edge(),
            event_end=self.right_edge(),
            annotation_done=self.is_done(),
            recorded=self.is_recorded(),
        )

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

    def __init__(self, parent=None):
        super().__init__(parent)
        self.plot_widget = PlotWidget()
        self.main_layout = QHBoxLayout()
        self.edit_layout = QVBoxLayout()
        self.add_layout = QGridLayout()
        # region items mapped as {LinearRegionItem: RegionEditWidget}
        self.region_edit_map = dict()
        self.add_groupbox = QGroupBox('Add/remove events')
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
        self.add_groupbox.setLayout(self.add_layout)
        self.edit_layout.addWidget(self.add_groupbox)
        self.add_button.clicked.connect(self.add_button_clicked)
        self.remove_all_button.clicked.connect(self.remove_all)

    @property
    def x_arr(self):
        """ Plot x values property. """
        return self.plot_widget.x_arr

    @property
    def y_arr(self):
        """ Plot y values property. """
        return self.plot_widget.y_arr

    def plot(self, x_arr, y_arr, mode: PlotMode = PlotMode.OVERWRITE):
        """
        Plot (x, y) data.

        :param x_arr:
        :param y_arr:
        :param mode:
        :return:
        """
        return self.plot_widget.plot(x_arr, y_arr, mode)

    def region_count(self) -> int:
        """
        Return number of regions.

        :return:
        """
        return len(self.region_edit_map)

    def get_add_count(self) -> int:
        """
        Return value from the add count widget.

        :return:
        """
        return self.add_count.value()

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
            return [
                key
                for key, value in self.region_edit_map.items()
                if value == edit_widget
            ][0]
        except IndexError:
            raise ValueError('No matching edit widget found')

    def add_region(
        self,
        edges: Tuple[float, float],
        bounds: Tuple[float, float] = None,
        movable: bool = True,
    ) -> RegionEditWidget:
        """
        Add a region to the plot.

        :param edges: Region edges
        :param bounds: Region bounds
        :param movable:
        :return:
        """
        if bounds is None:
            bounds = [min(self.x_arr), max(self.x_arr)]
        alpha = 125
        color = list(color_palette[len(self.region_edit_map)]) + [alpha]
        item = pg.LinearRegionItem(
            edges, bounds=bounds, movable=movable, brush=pg.mkBrush(*color)
        )
        self.plot_widget.addItem(item)
        # Event numbering by insertion order
        edit_widget = RegionEditWidget(item, event_number=self.region_count() + 1)
        edit_widget.remove_button.clicked.connect(
            partial(self.remove_region, edit_widget)
        )
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
        count = self.get_add_count()
        logger.debug(f'{type(self).__name__} add button clicked (add count={count})')
        if len(self.x_arr) == 0:
            logger.error('Unable to add region to empty plot')
            return 0
        if count > 0:
            x_min = min(self.x_arr)
            interval = (max(self.x_arr) - x_min) / count
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
        return [
            self.get_region_edit(i).get_annotated_event()
            for i in range(self.region_count())
        ]


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
        from cranio.constants import PLOT_N_SECONDS

        if self.find_plot_widget_by_label(label) is not None:
            raise ValueError('A plot widget with label {} already exists'.format(label))
        # If placeholder exists, use it
        # NOTE: No need to add to layout as placeholder is there by default
        if self.placeholder is not None:
            plot_widget = self.placeholder
            self.placeholder = None
        # If no placeholder exists, create new
        else:
            plot_widget = PlotWidget()
            self.main_layout.addWidget(plot_widget)
        plot_widget.y_label = label
        # Add filter defined by PLOT_N_SECONDS
        if PLOT_N_SECONDS is not None:
            plot_widget.add_filter(partial(filter_last_n_seconds, n=PLOT_N_SECONDS))
        self.plot_widgets.append(plot_widget)
        return plot_widget

    def plot(
        self, df: pd.DataFrame, title: str = '', mode: PlotMode = PlotMode.OVERWRITE
    ):
        """
        Plot a dataframe.

        :param df: Pandas DataFrame where index is the x axis.
        :param title: Plot title.
        :param mode:
        :return:
        """
        # Data is stored as a DataFrame
        # The DataFrame is appended during recording
        # The real-time plot is updated at specified intervals
        self.title = title
        # Find already initialized columns
        initialized_columns = [p.y_label for p in self.plot_widgets if p.y_label in df]
        # Leftover columns need to be initialized
        non_initialized_columns = filter(
            lambda c: c not in initialized_columns, df.columns
        )
        for c in non_initialized_columns:
            self.add_plot_widget(c)
        # Plot each column
        for c in df:
            plot_widget = self.find_plot_widget_by_label(c)
            plot_widget.plot(x=df.index, y=df[c], mode=mode)

    def clear(self):
        """
        Clear all plots.

        :return:
        """
        for p in self.plot_widgets:
            p.clear_plot()

    def reset(self):
        """
        Remove all plots from the layout.

        :return:
        """
        for p in self.plot_widgets:
            remove_widget_from_layout(self.main_layout, p)
        self.plot_widgets = []
