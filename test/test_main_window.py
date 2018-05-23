from cranio.app import app
from sqlalchemy import exists
from sqlalchemy.exc import IntegrityError
from cranio.database import Patient, session_scope
from PyQt5.QtWidgets import (QMainWindow, QAction, QWidget, QDialog, QVBoxLayout, QInputDialog, QMessageBox,
                             QListWidget, QHBoxLayout, QPushButton)


def create_document():
    print('New document!')


def load_document():
    print('Load document!')


def add_patient(patient_id: str) -> Patient:
    '''
    Add new patient record to the database.
    Raises sqlalchemy.exc.IntegrityError if a record with the given patient_id already exists.
    '''
    patient = Patient(id=patient_id)
    with session_scope() as session:
        session.add(patient)
    return patient


def patient_exists(patient_id: str) -> bool:
    ''' Check if a given patient id already exists in the database '''
    with session_scope() as session:
        return session.query(exists().where(Patient.id == patient_id)).scalar()


class CreatePatientWidget(QWidget):
    '''
    TODO: Make this a list where user can easily delete and add new patients
    Addition by clicking on an empty row and writing the patient_id
    Removal by clicking on an existing row and hitting delete/right clicking and selecting delete
    Possible widget/view types: ListView, TableView
    '''

    def __init__(self):
        super().__init__()
        self.main_layout = QVBoxLayout()
        self.list_widget = QListWidget()
        self.main_layout.addWidget(self.list_widget)
        self.add_button = QPushButton('Add', parent=self)
        self.remove_button = QPushButton('Remove', parent=self)
        self.button_layout = QHBoxLayout()
        self.button_layout.addWidget(self.add_button)
        self.button_layout.addWidget(self.remove_button)
        self.main_layout.addLayout(self.button_layout)
        self.setLayout(self.main_layout)
        self.update_patients()

    def update_patients(self):
        ''' Updates the patient list '''
        self.list_widget.clear()
        with session_scope() as session:
            for patient in session.query(Patient).all():
                self.list_widget.addItem(patient.id)


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
        self.new_patient_action = QAction('New patient', self)
        self.new_patient_action.triggered.connect(self.create_patient)
        self.file_menu.addAction(self.new_patient_action)
        self.get_patients_action = QAction('Patients', self)
        self.get_patients_action.triggered.connect(self.get_patients)
        self.file_menu.addAction(self.get_patients_action)

    def create_patient(self):
        # open create patient dialog
        patient_id, ok = QInputDialog.getText(self, 'Create patient', 'Enter patient id:')
        if not ok:
            return
        # try to insert patient to database
        try:
            add_patient(patient_id)
        except IntegrityError:
            QMessageBox.information(self, 'Already exists',
                                    'Patient id "{}" already exists in the database'.format(patient_id))

    def get_patients(self):
        with session_scope() as session:
            patients = session.query(Patient).all()
        dialog = QDialog()
        layout = QVBoxLayout()
        widget = CreatePatientWidget()
        layout.addWidget(widget)
        dialog.setLayout(layout)
        dialog.exec_()


if __name__ == '__main__':
    #w = MainWindow()
    #w.show()
    #app.exec_()
    dialog = QDialog()
    layout = QVBoxLayout()
    widget = CreatePatientWidget()
    layout.addWidget(widget)
    dialog.setLayout(layout)
    dialog.exec_()
