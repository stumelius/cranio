"""
System states.
"""
from typing import List
from PyQt5.QtCore import QState, QEvent
from PyQt5.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QInputDialog
from cranio.app.window import MainWindow, RegionPlotWindow, NotesWindow, SessionDialog, PatientDialog
from cranio.app.widget import SessionWidget, PatientWidget
from cranio.model import session_scope, Session, Document, AnnotatedEvent, SensorInfo, DistractorType, Database
from cranio.utils import logger, utc_datetime
from cranio.producer import ProducerProcess


class StateMachineContextMixin:
    @property
    def database(self) -> Database:
        """ Context Database. """
        return self.machine().database

    @property
    def main_window(self) -> MainWindow:
        """ Context MainWindow. """
        return self.machine().main_window

    @property
    def document(self) -> Document:
        """ Context Document. """
        return self.machine().document

    @document.setter
    def document(self, value: Document):
        self.machine().document = value

    @property
    def annotated_events(self) -> List[AnnotatedEvent]:
        return self.machine().annotated_events

    @annotated_events.setter
    def annotated_events(self, values: List[AnnotatedEvent]):
        self.machine().annotated_events = values


class MyState(QState, StateMachineContextMixin):
    def __init__(self, name: str, parent=None):
        super().__init__(parent)
        self.name = name

    def __str__(self):
        return f'{type(self).__name__}(name="{self.name}")'

    def onEntry(self, event: QEvent):
        logger.debug(f'Enter {self.name}')

    def onExit(self, event: QEvent):
        logger.debug(f'Exit {self.name}')


class InitialState(MyState):
    def __init__(self, name: str, parent=None):
        super().__init__(name=name, parent=parent)

    @property
    def signal_change_session(self):
        return self.main_window.signal_change_session

    @property
    def signal_show_patients(self):
        return self.main_window.signal_show_patients

    def onEntry(self, event: QEvent):
        super().onEntry(event)
        self.main_window.show()
        # Set focus on Start button so that pressing Enter will trigger it
        logger.debug('Set focus on Start button')
        self.main_window.measurement_widget.stop_button.setDefault(False)
        self.main_window.measurement_widget.start_button.setDefault(True)
        self.main_window.measurement_widget.start_button.setFocus()


class ChangeSessionState(MyState):
    def __init__(self, name: str, parent=None):
        super().__init__(name=name, parent=parent)
        # UI elements are not initialized here because self.database is undefined before assignment to a state machine
        self.session_widget = None
        self.session_dialog = None
        self.signal_select = None
        self.signal_cancel = None

    def init_ui(self):
        """ Initialize UI elements. Needs to be called before entry. """
        self.session_widget = SessionWidget(database=self.database)
        self.session_dialog = SessionDialog(self.session_widget)
        self.signal_select = self.session_widget.select_button.clicked
        self.signal_cancel = self.session_widget.cancel_button.clicked
        # Close equals to Cancel
        self.session_dialog.signal_close = self.signal_cancel

    def active_session_id(self):
        return self.session_widget.active_session_id()

    def onEntry(self, event: QEvent):
        super().onEntry(event)
        # Keep selection, update and open dialog
        session_id = self.session_widget.active_session_id()
        self.session_widget.update_sessions()
        if session_id is not None:
            self.session_widget.select_session(session_id)
        self.session_dialog.show()

    def onExit(self, event: QEvent):
        super().onExit(event)
        # Close dialog
        self.session_dialog.close()


class MeasurementState(MyState):
    def __init__(self, name: str, parent=None):
        super().__init__(name=name, parent=parent)

    def create_document(self) -> Document:
        """
        Create a Document object from context.

        :return:
        :raises ValueError: if active patient is invalid
        """
        # FIXME: KLS distractor by default
        return Document(session_id=Session.get_instance().session_id, patient_id=self.machine().active_patient,
                        distractor_number=self.machine().active_distractor, operator=self.machine().active_operator,
                        started_at=utc_datetime(),
                        sensor_serial_number=self.machine().sensor.sensor_info.sensor_serial_number,
                        distractor_type=DistractorType.KLS)

    def onEntry(self, event: QEvent):
        super().onEntry(event)
        # MeasurementStateTransition ensures that only one sensor is connected
        sensor = self.machine().sensor
        # Create new document
        self.document = self.create_document()
        self.main_window.measurement_widget.update_timer.start(self.main_window.measurement_widget.update_interval*1000)
        # Clear plot
        logger.debug('Clear plot')
        self.main_window.measurement_widget.clear()
        # Insert sensor info and document to database
        sensor.enter_info_to_database(self.database)
        logger.debug(f'Enter document: {str(self.document)}')
        self.database.insert(self.document)
        # Kill old producer process
        if self.main_window.producer_process is not None:
            self.main_window.producer_process.join()
        # Create producer process and register connected sensor
        self.main_window.producer_process = ProducerProcess('Imada torque producer', document=self.document)
        self.main_window.register_sensor_with_producer()
        # Start producing!
        self.main_window.measurement_widget.producer_process.start()
        # Set focus on Start button so that pressing Enter will trigger it
        logger.debug('Set focus on Stop button')
        self.main_window.measurement_widget.start_button.setDefault(False)
        self.main_window.measurement_widget.stop_button.setDefault(True)
        self.main_window.measurement_widget.stop_button.setFocus()

    def onExit(self, event: QEvent):
        super().onExit(event)
        # Pause producer process and stop timer
        if self.main_window.measurement_widget.producer_process is None:
            return
        self.main_window.measurement_widget.producer_process.pause()
        self.main_window.measurement_widget.update_timer.stop()
        # Update to ensure that all data is inserted to database
        self.main_window.measurement_widget.update()


class EventDetectionState(MyState):

    def __init__(self, name: str, parent=None):
        super().__init__(name=name, parent=parent)
        self.dialog = RegionPlotWindow()
        # Signals
        self.signal_ok = self.dialog.ok_button.clicked
        self.signal_add = self.dialog.add_button.clicked
        self.signal_value_changed = self.dialog.signal_value_changed
        self.signal_close = self.dialog.signal_close

    def onEntry(self, event: QEvent):
        """
        Open a RegionPlotWindow and plot context document data.

        :param event:
        :return:
        """
        super().onEntry(event)
        self.dialog.plot(*self.document.get_related_time_series(self.database))
        # Clear existing regions
        self.dialog.clear_regions()
        # Add as many regions as there are turns in one full turn
        sensor_info = self.document.get_related_sensor_info(self.database)
        self.dialog.set_add_count(int(sensor_info.turns_in_full_turn))
        self.dialog.add_button.clicked.emit(True)
        self.dialog.show()

    def onExit(self, event: QEvent):
        super().onExit(event)
        self.dialog.close()

    def region_count(self) -> int:
        """ Return number of regions. """
        return self.dialog.region_count()

    def get_annotated_events(self) -> List[AnnotatedEvent]:
        """ Return list of annotated events. """
        return self.dialog.get_annotated_events()


class AreYouSureState(MyState):

    def __init__(self, text_template: str, name: str=None, parent=None):
        """

        :param text: Text shown in the dialog
        :param name:
        :param parent:
        """
        if name is None:
            name = type(self).__name__
        super().__init__(name=name, parent=parent)
        self.template = text_template
        self.dialog = QMessageBox()
        self.yes_button = self.dialog.addButton('Yes', QMessageBox.YesRole)
        self.no_button = self.dialog.addButton('No', QMessageBox.NoRole)
        self.dialog.setIcon(QMessageBox.Question)
        self.dialog.setWindowTitle('Are you sure?')
        # Signals
        self.signal_yes = self.yes_button.clicked
        self.signal_no = self.no_button.clicked

    def namespace(self) -> dict:
        """ Return template namespace. """
        try:
            region_count = len(self.annotated_events)
        except (AttributeError, TypeError):
            # Object has no attribute 'annotated_events' or annotated_events = None
            region_count = None
        try:
            session_info = self.machine().s9.session_widget.active_session_id
        except AttributeError:
            # 'NoneType' object has no attribute 's9'
            session_info = None
        return {'region_count': region_count, 'session_info': session_info}

    def onEntry(self, event: QEvent):
        super().onEntry(event)
        # Set focus on Yes button so that pressing Enter will trigger it
        self.yes_button.setDefault(True)
        self.no_button.setDefault(False)
        self.dialog.setText(self.template.format(**self.namespace()))
        self.dialog.open()

    def onExit(self, event: QEvent):
        super().onExit(event)
        self.dialog.close()


class NoteState(MyState):
    def __init__(self, name: str, parent=None):
        super().__init__(name=name, parent=parent)
        self.dialog = NotesWindow()
        # Signals
        self.signal_ok = self.dialog.ok_button.clicked
        self.signal_close = self.dialog.signal_close

    def onEntry(self, event: QEvent):
        super().onEntry(event)
        # Set default full turn count
        event_count = len(self.document.get_related_events(self.database))
        with session_scope(self.database) as s:
            sensor_info = s.query(SensorInfo).\
                filter(SensorInfo.sensor_serial_number == self.document.sensor_serial_number).first()
        self.full_turn_count = event_count / float(sensor_info.turns_in_full_turn)
        logger.debug(f'Calculate default full_turn_count = {self.full_turn_count} = '
                     f'{event_count} / {sensor_info.turns_in_full_turn}')
        self.dialog.open()

    def onExit(self, event: QEvent):
        super().onExit(event)
        # Update document and close window
        self.document.notes = self.dialog.notes
        self.document.full_turn_count = self.dialog.full_turn_count
        self.dialog.close()

    @property
    def full_turn_count(self):
        return self.dialog.full_turn_count

    @full_turn_count.setter
    def full_turn_count(self, value):
        self.dialog.full_turn_count = value


class ShowPatientsState(MyState):
    def __init__(self, name: str, parent=None):
        super().__init__(name=name, parent=parent)
        # UI elements are not initialized here because self.database is undefined before assignment to a state machine
        self.dialog = None
        self.patient_widget = None
        self.signal_add_patient = None
        self.signal_close = None

    def init_ui(self):
        """ Initialize UI elements. Needs to be called before entry. """
        self.patient_widget = PatientWidget(database=self.database)
        self.dialog = PatientDialog(patient_widget=self.patient_widget)
        self.signal_add_patient = self.patient_widget.add_button.clicked
        self.signal_close = self.dialog.signal_close

    def onEntry(self, event: QEvent):
        super().onEntry(event)
        self.patient_widget.update_patients()
        self.dialog.open()

    def onExit(self, event: QEvent):
        super().onExit(event)
        self.dialog.close()


class AddPatientState(MyState):
    def __init__(self, name: str, parent=None):
        super().__init__(name=name, parent=parent)
        self.dialog = QInputDialog()
        self.dialog.setWindowTitle('Add patient')
        self.dialog.setLabelText('Enter patient id:')
        self.signal_cancel = self.dialog.rejected
        self.signal_ok = self.dialog.accepted

    def onEntry(self, event: QEvent):
        super().onEntry(event)
        self.dialog.open()

    def onExit(self, event: QEvent):
        super().onExit(event)
        self.dialog.close()