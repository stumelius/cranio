"""
.. todo:: Refactor GUI modules (#90)
"""
import pandas as pd
import logging
from typing import List
from functools import partial
from PyQt5 import QtCore
from PyQt5.QtWidgets import (QGroupBox, QVBoxLayout, QPushButton, 
                             QSpinBox, QMessageBox, QWidget,
                             QLineEdit, QHBoxLayout, QLabel, 
                             QDialog, QAction, QInputDialog, QComboBox,
                             QMainWindow, QTableWidget, QTableWidgetItem, QAbstractItemView)
from sqlalchemy.exc import IntegrityError
from daqstore.store import DataStore
from cranio.app.plot import VMultiPlotWidget, RegionPlotWindow
from cranio.database import session_scope, Patient
from cranio.producer import ProducerProcess, plug_dummy_sensor
from cranio.imada import plug_imada

PATIENT_ID_TOOLTIP = ('Enter patient identifier.\n'
                      'NOTE: Do not enter personal information, such as names.')
SESSION_ID_TOOLTIP = ('This is a random-generated unique identifier.\n'
                      'NOTE: Value cannot be changed by the user.')
DISTRACTOR_ID_TOOLTIP = 'Enter distractor identifier/number.'


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

    def set_range(self, min: int, max:int):
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
    
    def __init__(self, parent=None):
        super().__init__(parent=parent)
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
        self.distractor_widget.value = 1
        self.distractor_widget.set_range(1, 10)
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
    def active_patient(self, value: str):
        self.patient_widget.value = value

    def toggle_lock_button_clicked(self):
        """
        Toggle patient widget lock.

        :return:
        """
        self.enabled = not self.enabled
        self.patient_widget.setEnabled(self.enabled)
        logging.debug(f'Toggle Lock button clicked (enabled={self.enabled})')


def create_document():
    """ Dummy function. """
    logging.info('create_document() called!')


def load_document():
    """ Dummy function. """
    logging.info('load_document() called!')


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

    def __init__(self, producer_process=None, parent=None):
        super().__init__(parent)
        self.producer_process = producer_process
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
        window = RegionPlotWindow(self)
        if len(self.multiplot_widget.plot_widgets) > 1:
            raise NotImplementedError('No support for over 2-dimensional data')
        for p in self.multiplot_widget.plot_widgets:
            # copy plot widget
            p_new = window.plot(x=p.x, y=p.y)
            p_new.y_label = p.y_label
        window.exec_()

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
