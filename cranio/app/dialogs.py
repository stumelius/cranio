'''
This module implements the graphical user interface elements of the craniodistractor application.

Copyright (C) 2017  Simo Tumelius

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''
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
from daqstore.store import DataStore
from cranio.app.plot import PlotWindow, VMultiPlotWidget, RegionPlotWindow
from cranio.core import generate_unique_id
from cranio.database import session_scope, IntegrityError, Patient
from cranio.producer import ProducerProcess, plug_dummy_sensor
from cranio.imada import plug_imada_sensor

PATIENT_ID_TOOLTIP = ('Enter patient identifier.\n'
                      'NOTE: Do not enter personal information, such as names.')
SESSION_ID_TOOLTIP = ('This is a random-generated unique identifier.\n'
                      'NOTE: Value cannot be changed by the user.')


class EditWidget(QWidget):
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
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.edit_widget)
        self.setLayout(self.layout)
        
    @property
    def value(self):
        return self.edit_widget.text()
    
    @value.setter
    def value(self, value):
        self.edit_widget.setText(value)
        
    @property
    def tooltip(self):
        return self.edit_widget.toolTip()
    
    @tooltip.setter
    def tooltip(self, text):
        self.edit_widget.setToolTip(text)


class ComboEditWidget(EditWidget):
    _edit_widget_cls = QComboBox

    def add_item(self, text: str):
        self.edit_widget.addItem(text)

    def set_item(self, index: int, text: str):
        self.edit_widget.setItemText(index, text)

    def clear(self):
        self.edit_widget.clear()

    def count(self):
        return self.edit_widget.count()

    def item_at(self, index: int):
        return self.edit_widget.itemText(index)

    @property
    def value(self):
        return self.edit_widget.currentText()

    @value.setter
    def value(self, value):
        self.edit_widget.setEditText(value)


class SessionMetaWidget(QGroupBox):
    closing = QtCore.pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.patient_widget = ComboEditWidget('Patient', parent=self)
        # initialize session as unique id
        self.session_widget = EditWidget('Session', generate_unique_id(), self)
        self.toggle_lock_button = QPushButton('Toggle Lock')
        self.layout = QVBoxLayout()
        self.enabled = True
        self.init_ui()
        
    def init_ui(self):
        self.toggle_lock_button.clicked.connect(self.toggle_lock_button_clicked)
        self.layout.addWidget(self.patient_widget)
        self.layout.addWidget(self.session_widget)
        self.layout.addWidget(self.toggle_lock_button)
        self.setLayout(self.layout)
        self.setTitle('Session information')
        # disable changes to session
        self.session_widget.setDisabled(True)
        # set tooltips
        self.patient_widget.tooltip = PATIENT_ID_TOOLTIP
        self.session_widget.tooltip = SESSION_ID_TOOLTIP

    def add_patient(self, text: str):
        '''
        Add patient to combo box.

        :param text:
        :return:
        '''
        self.patient_widget.add_item(text)

    def update_patients_from_database(self):
        '''
        Clear and populate patient combo box from database.

        :return:
        '''
        logging.debug('Update patients called')
        self.patient_widget.clear()
        with session_scope() as s:
            for p in s.query(Patient).all():
                # populate patient widget
                logging.debug(f'patient_id = {p.patient_id}')
                self.patient_widget.add_item(p.patient_id)

    def patients(self) -> List[str]:
        '''

        :return: List of patient IDs
        '''
        return [self.patient_widget.item_at(i) for i in range(self.patient_widget.count())]

    @property
    def active_patient(self) -> str:
        return self.patient_widget.value
    
    @active_patient.setter
    def active_patient(self, value: str):
        self.patient_widget.value = value

    def toggle_lock_button_clicked(self):
        self.enabled = not self.enabled
        self.patient_widget.setEnabled(self.enabled)
        logging.debug(f'Toggle Lock button clicked (enabled={self.enabled})')


class MeasurementDialog(PlotWindow):
    
    def __init__(self, producer_process=None):
        self.distractor_group_box = QGroupBox()
        self.distractor_group_box_layout = QVBoxLayout()
        self.distractor_edit = QSpinBox()
        super(MeasurementDialog, self).__init__(producer_process)
        
    def init_ui(self):
        super(MeasurementDialog, self).init_ui()
        self.setWindowTitle('Measurement dialog')
        self.distractor_group_box_layout.addWidget(self.distractor_edit)
        self.distractor_group_box.setLayout(self.distractor_group_box_layout)
        self.main_layout.insertWidget(0, self.distractor_group_box)
        self.distractor_group_box.setTitle('Distractor index')
    
    @property  
    def distractor_index(self):
        return self.distractor_edit.value()
    
    @distractor_index.setter
    def distractor_index(self, value):
        if not isinstance(value, int):
            raise ValueError('Distractor index must be an integer')
        self.distractor_edit.setValue(value)
        
    def start_button_clicked(self):
        ''' Confirm that user wants to start the measurement '''
        message = (f'You entered {self.distractor_index} as the distractor index.\n'
                   'Are you sure you want to start the measurement?')
        if QMessageBox.question(self, 'Are you sure?', message) == QMessageBox.Yes:
            super().start_button_clicked()


def create_document():
    print('New document!')


def load_document():
    print('Load document!')


def add_patient(patient_id: str) -> Patient:
    '''
    Add new patient record to the database.
    Raises sqlalchemy.exc.IntegrityError if a record with the given patient_id already exists.
    '''
    patient = Patient(patient_id=patient_id)
    with session_scope() as session:
        session.add(patient)
    return patient


def prompt_create_patient(parent_widget) -> str:
    '''
    Prompt the user to create a new patient id.
    The patient is inserted to the database if no constraints are violated.
    Returns:
        patient identifier string or None if no patient was created (user cancelled or constraint violation)
    '''
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
                                'Patient id "{}" is invalid or already exists in the database'.format(patient_id))


class PatientWidget(QWidget):
    '''
    Addition by clicking on an empty row and writing the patient_id.
    Removal is not supported by the widget and is only possible by directly querying the database.
    Possible widget/view types: ListView, TableView
    '''

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
        ''' Updates the patient list '''
        with session_scope() as session:
            for i, patient in enumerate(session.query(Patient).all()):
                self.table_widget.setRowCount(i + 1)
                self.table_widget.setItem(i, 0, QTableWidgetItem(patient.patient_id))
                self.table_widget.setItem(i, 1, QTableWidgetItem(str(patient.created_at)))

    def add_patient(self, patient_id: str):
        add_patient(patient_id)
        self.update_patients()

    def add_button_clicked(self):
        prompt_create_patient(self)
        self.update_patients()

    def patient_count(self):
        return self.table_widget.rowCount()


class MeasurementWidget(QWidget):
    ''' A window for plot widgets '''

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
        self.multiplot_widget.plot(df)

    def add_plot(self, label: str):
        ''' Adds a plot widget to the window '''
        return self.multiplot_widget.add_plot_widget(label)

    def get_plot(self, label: str):
        ''' Alternative for plot_window[index] '''
        return self.multiplot_widget.find_plot_widget_by_label(label)

    def update(self):
        '''
        Reads data from a producer and appends that to the plot.

        Args:
            None

        Returns:
            None

        Raises:
            None
        '''
        self.producer_process.store.read()
        self.producer_process.store.flush()
        data = self.producer_process.read()
        self.plot(data)

    @QtCore.pyqtSlot()
    def ok_button_clicked(self):
        '''
        Create and show a modal RegionWindow containing the plotted data.

        Args:
            None

        Returns:
            None

        Raises:
            None
        '''
        window = RegionPlotWindow(self)
        if len(self.multiplot_widget.plot_widgets) > 1:
            raise NotImplementedError('No support for over 2-dimensional data')
        for p in self.multiplot_widget.plot_widgets:
            # copy plot widget
            p_new = window.plot(x=p.x, y=p.y)
            p_new.y_label = p.y_label
        window.exec_()

    def start_button_clicked(self):
        '''
        Starts the producer process if is not None. Otherwise, nothing happens.
        Ok button is disabled. Emits signal: started.

        Args:
            None

        Returns:
            None

        Raises:
            None
        '''
        if self.producer_process is None:
            QMessageBox.critical(self, 'Error', 'No producer process defined')
            return
        self.update_timer.start(self.update_interval * 1000)
        self.producer_process.start()
        self.started.emit()
        self.ok_button.setEnabled(False)

    def stop_button_clicked(self):
        '''
        Stop the producer process if is not None. Otherwise, nothing happens.
        Ok button is enabled. Emits signal: stopped.

        Args:
            None

        Returns:
            None

        Raises:
            None
        '''
        if self.producer_process is None:
            return
        self.producer_process.pause()
        self.update_timer.stop()
        self.stopped.emit()
        self.ok_button.setEnabled(True)


class MainWindow(QMainWindow):

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
        self.meta_widget = SessionMetaWidget()
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
        self.connect_torque_sensor_action.triggered.connect(partial(plug_imada_sensor, self.producer_process))
        self.connect_dummy_sensor_action = QAction('Connect dummy torque sensor', self)
        self.connect_dummy_sensor_action.triggered.connect(partial(plug_dummy_sensor, self.producer_process))
        self.connect_menu.addAction(self.connect_torque_sensor_action)
        self.connect_menu.addAction(self.connect_dummy_sensor_action)
        self.init_ui()

    def init_ui(self):
        self.meta_widget.update_patients_from_database()


    def open_patient_widget(self):
        with session_scope() as session:
            patients = session.query(Patient).all()
        dialog = QDialog(parent=self)
        layout = QVBoxLayout()
        widget = PatientWidget()
        layout.addWidget(widget)
        dialog.setLayout(layout)
        dialog.exec_()
        self.meta_widget.update_patients_from_database()
