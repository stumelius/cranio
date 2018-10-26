"""
.. todo:: To be documented.
"""
from typing import List
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QAction, QMainWindow, QWidget, QDialog, QVBoxLayout, QPushButton
from cranio.producer import ProducerProcess, create_dummy_sensor
from cranio.imada import Imada
from cranio.database import session_scope, Patient, AnnotatedEvent
from cranio.app.widget import PatientWidget, MetaDataWidget, MeasurementWidget, RegionPlotWidget, EditWidget, \
    DoubleSpinEditWidget, SessionWidget
from cranio.utils import logger


def create_document():
    """ Dummy function. """
    logger.info('create_document() called!')


def load_document():
    """ Dummy function. """
    logger.info('load_document() called!')


class RegionPlotWindow(QDialog):
    """ Dialog with a region plot widget and an "Ok" button. """
    signal_close = pyqtSignal()

    def __init__(self, parent=None):
        """

        :param parent:
        """
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.region_plot_widget = RegionPlotWidget()
        self.notes_window = NotesWindow()
        self.ok_button = QPushButton('Ok')
        self.add_button = self.region_plot_widget.add_button
        self.signal_value_changed = self.region_plot_widget.add_count.valueChanged
        self.init_ui()

    def init_ui(self):
        """ Initialize UI elements. """
        self.setWindowTitle('Region window')
        # Add maximize button
        self.setWindowFlag(Qt.WindowMinMaxButtonsHint)
        self.setLayout(self.layout)
        self.layout.addWidget(self.region_plot_widget)
        self.layout.addWidget(self.ok_button)
        self.ok_button.clicked.connect(self.ok_button_clicked)
        # Update focus when Add is clicked
        self.add_button.clicked.connect(self.update_focus)

    def keyPressEvent(self, event):
        # Increase add count when up arrow is pressed
        if event.key() == Qt.Key_Up:
            n = self.get_add_count() + 1
            logger.debug(f'Increase add count to {n} (Up arrow pressed)')
            self.set_add_count(n)
        # Decrease add count when up arrow is pressed
        elif event.key() == Qt.Key_Down:
            n = self.get_add_count() - 1
            logger.debug(f'Decrease add count to {n} (Down arrow pressed)')
            self.set_add_count(n)
        return super().keyPressEvent(event)

    @property
    def x_arr(self):
        """ Overload property. """
        return self.region_plot_widget.x_arr

    @property
    def y_arr(self):
        """ Overload property. """
        return self.region_plot_widget.y_arr

    def get_annotated_events(self) -> List[AnnotatedEvent]:
        return self.region_plot_widget.get_annotated_events()

    def plot(self, x, y):
        """ Overload method. """
        return self.region_plot_widget.plot(x, y)

    def get_add_count(self) -> int:
        return self.region_plot_widget.get_add_count()

    def set_add_count(self, value: int):
        """ Overload method. """
        # TODO: Replace getter and setter with property
        return self.region_plot_widget.set_add_count(value)

    def get_region_edit(self, index: int):
        """ Overload method. """
        return self.region_plot_widget.get_region_edit(index)

    def region_count(self) -> int:
        """ Overload method. """
        return self.region_plot_widget.region_count()

    def clear_regions(self):
        logger.debug('Clear regions')
        ret = self.region_plot_widget.remove_all()
        self.update_focus()
        return ret

    def update_focus(self):
        """
        If no regions have been entered, set focus on Add so that pressing Enter triggers it.
        Otherwise, set focus on Ok.

        :return:
        """
        if not self.region_count():
            logger.debug('Set focus on Add button')
            self.region_plot_widget.add_button.setDefault(True)
            self.ok_button.setDefault(False)
        else:
            logger.debug('Set focus on Ok button')
            self.region_plot_widget.add_button.setDefault(False)
            self.ok_button.setDefault(True)

    def ok_button_clicked(self):
        logger.debug('Ok button clicked')

    def closeEvent(self, event):
        """ User has clicked X on the dialog or QWidget.close() has been called programmatically. """
        super().closeEvent(event)
        logger.debug('X (close) button clicked')
        self.signal_close.emit()


class NotesWindow(QDialog):
    signal_close = pyqtSignal()

    def __init__(self):
        super().__init__()
        # layout and widgets
        self.layout = QVBoxLayout()
        self.notes_widget = EditWidget('Notes')
        self.full_turn_count_widget = DoubleSpinEditWidget('Number of full turns')
        self.ok_button = QPushButton('Ok')
        # initialize ui
        self.init_ui()

    def init_ui(self):
        """
        Initialize UI elements.

        :return:
        """
        self.setWindowTitle('Notes')
        self.layout.addWidget(self.full_turn_count_widget)
        self.layout.addWidget(self.notes_widget)
        self.layout.addWidget(self.ok_button)
        self.setLayout(self.layout)

    @property
    def full_turn_count(self) -> float:
        return self.full_turn_count_widget.value

    @full_turn_count.setter
    def full_turn_count(self, value: float):
        self.full_turn_count_widget.value = value

    @property
    def notes(self) -> str:
        return self.notes_widget.value

    @notes.setter
    def notes(self, value: str):
        self.notes_widget.value = value

    def closeEvent(self, event):
        """ User has clicked X on the dialog or QWidget.close() has been called programmatically. """
        super().closeEvent(event)
        logger.debug('X (close) button clicked')
        self.signal_close.emit()


class SessionDialog(QDialog):
    signal_close = pyqtSignal()

    def __init__(self, session_widget: SessionWidget):
        super().__init__()
        self.session_widget = session_widget
        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.session_widget)
        self.main_layout.addWidget(self.session_widget)
        self.setLayout(self.main_layout)

    def closeEvent(self, event):
        """ User has clicked X on the dialog or QWidget.close() has been called programmatically. """
        super().closeEvent(event)
        self.signal_close.emit()


class MainWindow(QMainWindow):
    """ Craniodistraction application main window. """
    signal_close = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Craniodistractor')
        self._producer_process = None
        self.sensor = None
        # Layouts
        self.main_layout = QVBoxLayout()
        self.main_widget = QWidget()
        self.main_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.main_widget)
        # Add meta prompt widget
        self.meta_widget = MetaDataWidget()
        self.main_layout.addWidget(self.meta_widget)
        # Add measurement widget
        self.measurement_widget = MeasurementWidget(producer_process=self.producer_process)
        self.main_layout.addWidget(self.measurement_widget)
        # Add File menu
        self.file_menu = self.menuBar().addMenu('File')
        self.add_patient_action = QAction('Add patient', self)
        self.add_patient_action.triggered.connect(self.open_patient_widget)
        self.file_menu.addAction(self.add_patient_action)
        self.change_session_action = QAction('Change session', self)
        self.file_menu.addAction(self.change_session_action)
        # Add Connect menu
        self.connect_menu = self.menuBar().addMenu('Connect')
        self.connect_torque_sensor_action = QAction('Connect Imada torque sensor', self)
        self.connect_torque_sensor_action.triggered.connect(self.connect_imada_sensor)
        self.connect_dummy_sensor_action = QAction('Connect dummy torque sensor', self)
        self.connect_dummy_sensor_action.triggered.connect(self.connect_dummy_sensor)
        self.connect_menu.addAction(self.connect_torque_sensor_action)
        self.connect_menu.addAction(self.connect_dummy_sensor_action)
        # Define signals
        self.signal_start = self.measurement_widget.start_button.clicked
        self.signal_stop = self.measurement_widget.stop_button.clicked
        self.signal_change_session = self.change_session_action.triggered
        self.init_ui()

    @property
    def producer_process(self):
        return self._producer_process

    @producer_process.setter
    def producer_process(self, value: ProducerProcess):
        self._producer_process = value
        logger.debug(f'Set measurement widget producer process to {self._producer_process}')
        self.measurement_widget.producer_process = self._producer_process

    def init_ui(self):
        """ Initialize UI elements. """
        self.meta_widget.update_patients_from_database()

    def open_patient_widget(self):
        """
        Open widget to view existing patients and add new ones.

        :return:
        """
        with session_scope() as session:
            patients = session.query(Patient).all()
        dialog = QDialog(parent=self)
        layout = QVBoxLayout()
        widget = PatientWidget()
        layout.addWidget(widget)
        dialog.setLayout(layout)
        dialog.exec_()
        self.meta_widget.update_patients_from_database()

    def set_patient(self, patient_id: str, lock: bool=False):
        """
        Set active patient.

        :param patient_id:
        :param lock: lock patient
        :return:
        """
        self.meta_widget.active_patient = patient_id
        self.meta_widget.lock_patient(lock)

    def get_patient(self) -> str:
        """
        Return active patient id.

        :return:
        """
        return self.meta_widget.active_patient

    def start_measurement(self):
        """
        Measure until stopped.

        :return:
        """
        return self.measurement_widget.start_button.clicked.emit(True)

    def stop_measurement(self):
        """
        Stop measurement.

        :return:
        """
        return self.measurement_widget.stop_button.clicked.emit(True)

    def click_ok(self):
        """
        Click Ok button.

        :return:
        """
        return self.measurement_widget.ok_button.clicked.emit(True)

    def connect_dummy_sensor(self):
        self.sensor = create_dummy_sensor()

    def connect_imada_sensor(self):
        self.sensor = Imada()

    def register_sensor_with_producer(self):
        if self.sensor is not None:
            self.producer_process.producer.register_sensor(self.sensor)

    def unregister_sensor(self):
        self.producer_process.producer.unregister_sensor(self.sensor)
        self.sensor = None

    def closeEvent(self, event):
        """ User has clicked X on the dialog or QWidget.close() has been called programmatically. """
        super().closeEvent(event)
        self.signal_close.emit()
