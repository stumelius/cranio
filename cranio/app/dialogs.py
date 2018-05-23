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
from PyQt5 import QtCore
from PyQt5.QtWidgets import (QGroupBox, QVBoxLayout, QPushButton, 
                             QSpinBox, QMessageBox, QWidget,
                             QLineEdit, QHBoxLayout, QLabel, 
                             QDialog)
from cranio.app.plot import PlotWindow
from cranio.core import generate_unique_id, SessionMeta

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
