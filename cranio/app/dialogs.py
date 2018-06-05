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
from functools import partial
from PyQt5 import QtCore
from PyQt5.QtWidgets import (QGroupBox, QVBoxLayout, QPushButton, 
                             QSpinBox, QMessageBox, QWidget,
                             QLineEdit, QHBoxLayout, QLabel, 
                             QDialog, QAction, QInputDialog,
                             QListWidget, QMainWindow, QTableWidget, QTableView, QTableWidgetItem)
from cranio.app.plot import PlotWindow
from cranio.core import generate_unique_id, SessionMeta
from cranio.database import session_scope, IntegrityError, Patient

PATIENT_ID_TOOLTIP = ('Enter patient identifier.\n'
                      'NOTE: Do not enter personal information, such as names.')
SESSION_ID_TOOLTIP = ('This is a random-generated unique identifier.\n'
                      'NOTE: Value cannot be changed by the user.')


class EditWidget(QWidget):
    
    def __init__(self, label, value=None, parent=None):
        super().__init__(parent)
        self.label = QLabel(label)
        self.edit_widget = QLineEdit()
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
        
class SessionMetaPromptWidget(QGroupBox):
    
    closing = QtCore.pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.patient_widget = EditWidget('Patient', parent=self)
        # initialize session as unique id
        self.session_widget = EditWidget('Session', generate_unique_id(), self)
        self.ok_button = QPushButton('Ok')
        self.layout = QVBoxLayout()
        self.init_ui()
        
    def init_ui(self):
        self.layout.addWidget(self.patient_widget)
        self.layout.addWidget(self.session_widget)
        self.layout.addWidget(self.ok_button)
        self.setLayout(self.layout)
        self.setTitle('Session information')
        self.ok_button.clicked.connect(self.ok_button_clicked)
        # disable changes to session
        self.session_widget.setDisabled(True)
        # set tooltips
        self.patient_widget.tooltip = PATIENT_ID_TOOLTIP
        self.session_widget.tooltip = SESSION_ID_TOOLTIP
    
    @property
    def patient(self):
        return self.patient_widget.value
    
    @patient.setter
    def patient(self, value):
        self.patient_widget.value = value
    
    @property
    def session(self):
        return self.session_widget.value
    
    @property
    def session_meta(self):
        return SessionMeta(self.patient, self.session)
        
    def ok_button_clicked(self):
        message = (f'You entered "{self.patient}" as the patient.\n'
                   'Are you sure you want to continue?')
        if QMessageBox.question(self, 'Are you sure?', message) == QMessageBox.Yes:
            self.closing.emit()
            self.close()


class SessionMetaDialog(QDialog):
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.prompt_widget = SessionMetaPromptWidget(parent=self)
        self.init_ui()
    
    def init_ui(self):
        self.layout.addWidget(self.prompt_widget)
        self.setLayout(self.layout)
        self.setWindowTitle('User input')
        # close dialog upon prompt widget close
        self.prompt_widget.closing.connect(self.accept)
        
    @property
    def session_meta(self):
        return self.prompt_widget.session_meta
        

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


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle('Craniodistractor application')
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

    def open_patient_widget(self):
        with session_scope() as session:
            patients = session.query(Patient).all()
        dialog = QDialog(parent=self)
        layout = QVBoxLayout()
        widget = PatientWidget()
        layout.addWidget(widget)
        dialog.setLayout(layout)
        dialog.exec_()
