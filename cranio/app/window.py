"""
.. todo:: To be documented.
"""
import logging
from functools import partial
from PyQt5.QtWidgets import QAction, QMainWindow, QWidget, QDialog, QVBoxLayout, QPushButton, QMessageBox
from daqstore.store import DataStore
from cranio.producer import ProducerProcess, plug_dummy_sensor
from cranio.imada import plug_imada
from cranio.database import Document, session_scope, Patient, Session
from cranio.app.widget import PatientWidget, MetaDataWidget, MeasurementWidget, RegionPlotWidget, EditWidget, \
    DoubleSpinEditWidget, CheckBoxEditWidget


def create_document():
    """ Dummy function. """
    logging.info('create_document() called!')


def load_document():
    """ Dummy function. """
    logging.info('load_document() called!')


class RegionPlotWindow(QDialog):
    """ Dialog with a region plot widget and an "Ok" button. """

    def __init__(self, document: Document, parent=None):
        """

        :param document: Data parent document
        :param parent:
        """
        super().__init__(parent)
        self.document = document
        self.layout = QVBoxLayout()
        self.region_plot_widget = RegionPlotWidget(document=self.document)
        self.notes_window = NotesWindow(document=self.document)
        self.ok_button = QPushButton('Ok')
        self.init_ui()

    def init_ui(self):
        """ Initialize UI elements. """
        self.setWindowTitle('Region window')
        self.setLayout(self.layout)
        self.layout.addWidget(self.region_plot_widget)
        self.layout.addWidget(self.ok_button)
        self.ok_button.clicked.connect(partial(self.ok_button_clicked, True))
        # plot document data
        self.plot(*self.document.get_related_time_series())

    def ok_button_clicked(self, user_prompt: bool = True):
        """
        :param user_prompt: Indicate if user is to be prompted for verification to continue.
            False can be used for testing purposes.
        :return:
        """
        msg = f'You have selected {self.region_plot_widget.region_count()} regions. Are you sure you want to continue?'
        if user_prompt:
            if not QMessageBox.question(self, 'Are you sure?', msg) == QMessageBox.Yes:
                return
        # insert annotated events to local database
        logging.debug('Get annotated events')
        events = self.region_plot_widget.get_annotated_events()
        for event in events:
            logging.debug(str(event.__dict__))
        logging.debug('Insert annotated events to database')
        try:
            with session_scope() as s:
                for e in events:
                    s.add(e)
        except Exception as e:
            logging.error(str(e))
        self.close()
        return self.notes_window.exec_()

    @property
    def x(self):
        """ Overload property. """
        return self.region_plot_widget.x

    @property
    def y(self):
        """ Overload property. """
        return self.region_plot_widget.y

    def plot(self, x, y):
        """ Overload method. """
        return self.region_plot_widget.plot(x, y)

    def set_add_count(self, value: int):
        """ Overload method. """
        return self.region_plot_widget.set_add_count(value)

    def add_button_clicked(self):
        """ Overload method. """
        return self.region_plot_widget.add_button_clicked()

    def get_region_edit(self, index: int):
        """ Overload method. """
        return self.region_plot_widget.get_region_edit(index)

    def region_count(self) -> int:
        """ Overload method. """
        return self.region_plot_widget.region_count()


class NotesWindow(QDialog):

    def __init__(self, document: Document):
        super().__init__()
        self.document = document
        self.layout = QVBoxLayout()
        self.notes_widget = EditWidget('Notes')
        self.distraction_achieved_widget = DoubleSpinEditWidget('Distraction achieved (mm)')
        self.distraction_plan_followed_widget = CheckBoxEditWidget('Distraction plan followed')
        self.ok_button = QPushButton('Ok')
        self.init_ui()

    def init_ui(self):
        """
        Initialize UI elements.

        :return:
        """
        self.setWindowTitle('Notes')
        self.layout.addWidget(self.distraction_plan_followed_widget)
        self.layout.addWidget(self.distraction_achieved_widget)
        self.layout.addWidget(self.notes_widget)
        self.layout.addWidget(self.ok_button)
        self.ok_button.clicked.connect(partial(self.ok_button_clicked, True))
        self.setLayout(self.layout)

    @property
    def notes(self):
        return self.notes_widget.value

    @notes.setter
    def notes(self, value: str):
        self.notes_widget.value = value
        self.document.notes = value

    @property
    def distraction_achieved(self):
        return self.distraction_achieved_widget.value

    @distraction_achieved.setter
    def distraction_achieved(self, value: float):
        self.distraction_achieved_widget.value = value
        self.document.distraction_achieved = value

    @property
    def distraction_plan_followed(self):
        return self.distraction_plan_followed_widget.value

    @distraction_plan_followed.setter
    def distraction_plan_followed(self, state: bool):
        self.distraction_plan_followed_widget.value = state
        self.document.distraction_plan_followed = state

    def ok_button_clicked(self, user_prompt: bool=True):
        msg = 'Are you sure you want to continue?'
        if user_prompt:
            if not QMessageBox.question(self, 'Are you sure?', msg) == QMessageBox.Yes:
                return
        self.close()


class MainWindow(QMainWindow):
    """ Craniodistraction application main window. """

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Craniodistractor')
        self.store = DataStore(buffer_length=10, resampling_frequency=None)
        self.producer_process = ProducerProcess('Imada torque producer', store=self.store)
        # layouts
        self.main_layout = QVBoxLayout()
        self.main_widget = QWidget()
        self.main_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.main_widget)
        # add meta prompt widget
        self.meta_widget = MetaDataWidget()
        self.main_layout.addWidget(self.meta_widget)
        # add measurement widget
        self.measurement_widget = MeasurementWidget(producer_process=self.producer_process)
        self.main_layout.addWidget(self.measurement_widget)
        # add File menu
        self.file_menu = self.menuBar().addMenu('File')
        self.new_document_action = QAction('New document', self)
        self.new_document_action.triggered.connect(create_document)
        self.file_menu.addAction(self.new_document_action)
        self.load_document_action = QAction('Load document', self)
        self.load_document_action.triggered.connect(load_document)
        self.file_menu.addAction(self.load_document_action)
        # add separator between documents and patients
        self.file_menu.addSeparator()
        self.patients_action = QAction('Patients', self)
        self.patients_action.triggered.connect(self.open_patient_widget)
        self.file_menu.addAction(self.patients_action)
        # add Connect menu
        self.connect_menu = self.menuBar().addMenu('Connect')
        self.connect_torque_sensor_action = QAction('Connect Imada torque sensor', self)
        self.connect_torque_sensor_action.triggered.connect(partial(plug_imada, self.producer_process))
        self.connect_dummy_sensor_action = QAction('Connect dummy torque sensor', self)
        self.connect_dummy_sensor_action.triggered.connect(partial(plug_dummy_sensor, self.producer_process))
        self.connect_menu.addAction(self.connect_torque_sensor_action)
        self.connect_menu.addAction(self.connect_dummy_sensor_action)
        # signals
        self.signal_start = self.measurement_widget.start_button.clicked
        self.signal_stop = self.measurement_widget.stop_button.clicked
        self.signal_ok = self.measurement_widget.ok_button.clicked
        self.init_ui()

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

