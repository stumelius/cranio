from typing import List
from PyQt5.QtCore import QStateMachine, QState, QEvent, pyqtSignal, QSignalTransition, QFinalState
from PyQt5.QtWidgets import QMessageBox
from cranio.app.window import MainWindow, RegionPlotWindow, NotesWindow, SessionDialog
from cranio.app.widget import SessionWidget
from cranio.database import session_scope, Session, Document, AnnotatedEvent, SensorInfo, DistractorType
from cranio.utils import logger, utc_datetime
from cranio.producer import ProducerProcess


class MyState(QState):

    def __init__(self, name: str, parent=None):
        super().__init__(parent)
        self.name = name

    def __str__(self):
        return f'{type(self).__name__}(name="{self.name}")'

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
        # Initialize session dialog
        self.session_widget = SessionWidget()
        self.session_dialog = SessionDialog(self.session_widget)
        # Define signals
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
        sensor.enter_info_to_database()
        with session_scope() as s:
            logger.debug(f'Enter document: {str(self.document)}')
            s.add(self.document)
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

    def onEntry(self, event: QEvent):
        """
        Open a RegionPlotWindow and plot context document data.

        :param event:
        :return:
        """
        super().onEntry(event)
        self.dialog.plot(*self.document.get_related_time_series())
        # Clear existing regions
        self.dialog.clear_regions()
        # Add as many regions as there are turns in one full turn
        sensor_info = self.document.get_related_sensor_info()
        self.dialog.set_add_count(int(sensor_info.turns_in_full_turn))
        self.dialog.add_button.clicked.emit(True)
        self.dialog.show()

    def onExit(self, event: QEvent):
        super().onExit(event)
        self.dialog.close()

    def region_count(self):
        return self.dialog.region_count()

    def get_annotated_events(self):
        return self.dialog.get_annotated_events()


class AreYouSureState(MyState):

    def __init__(self, text_template: str, name: str=None, parent=None):
        """

        :param text: Text shown in the dialog
        :param: name
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
        event_count = len(self.document.get_related_events())
        with session_scope() as s:
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


class StartMeasurementTransition(QSignalTransition):
    def eventTest(self, event: QEvent) -> bool:
        if not super().eventTest(event):
            return False
        # Invalid patient
        if not self.machine().active_patient:
            logger.error(f'Invalid patient "{self.machine().active_patient}"')
            return False
        # No sensor connected
        if self.machine().sensor is None:
            logger.error('No sensors connected')
            return False
        return True


class ChangeActiveSessionTransition(QSignalTransition):
    def onTransition(self, event: QEvent):
        super().onTransition(event)
        # Change active session
        session_id = self.machine().s9.active_session_id()
        logger.debug(f'[{type(self).__name__}] Change active session to {session_id}')
        with session_scope() as s:
            session = s.query(Session).filter(Session.session_id == session_id).first()
        self.machine().active_session = session


class EnterAnnotatedEventsTransition(QSignalTransition):
    def onTransition(self, event: QEvent):
        super().onTransition(event)
        # Assign annotated events and link to document
        logger.debug('Assign annotated events and link to document')
        self.machine().annotated_events = self.sourceState().get_annotated_events()
        for e in self.machine().annotated_events:
            e.document_id = self.machine().document.document_id
        logger.debug('Enter annotated events to database')
        with session_scope() as s:
            for e in self.machine().annotated_events:
                s.add(e)
                logger.debug(str(e))


class RemoveAnnotatedEventsTransition(QSignalTransition):
    def onTransition(self, event: QEvent):
        super().onTransition(event)
        with session_scope() as s:
            for e in self.machine().annotated_events:
                logger.debug(f'Remove {str(e)} from database')
                s.query(AnnotatedEvent).filter(AnnotatedEvent.document_id == e.document_id).\
                    filter(AnnotatedEvent.event_type == e.event_type).\
                    filter(AnnotatedEvent.event_num == e.event_num).delete()


class UpdateDocumentTransition(QSignalTransition):
    def onTransition(self, event: QEvent):
        super().onTransition(event)
        logger.debug('Update document in database')
        with session_scope() as s:
            document = s.query(Document).filter(Document.document_id == self.machine().document.document_id).first()
            document.notes = self.machine().document.notes
            document.full_turn_count = self.machine().document.full_turn_count
            logger.debug(str(document))


class MyStateMachine(QStateMachine):

    def __init__(self):
        super().__init__()
        # Initialize context
        self.main_window = MainWindow()
        self.document = None
        self.annotated_events = None
        # Initialize states
        self.s1 = InitialState(name='s1')
        self.s2 = MeasurementState(name='s2')
        self.s3 = EventDetectionState(name='s3')
        self.s6 = NoteState(name='s6')
        self.s7 = AreYouSureState('Are you sure you want to continue?', name='s7')
        self.s9 = ChangeSessionState(name='s9')
        self.s10 = AreYouSureState('You have selected session {session_info}. '
                                   'Are you sure you want to continue?', name='s10')
        self.s11 = AreYouSureState('Are you sure you want to exit the application?', name='s11')
        self.s0 = QFinalState()
        # Set states
        for s in (self.s0, self.s1, self.s2, self.s3, self.s6, self.s7, self.s9, self.s10, self.s11):
            self.addState(s)
        self.setInitialState(self.s1)
        # Define transitions
        self.start_measurement_transition = StartMeasurementTransition(self.main_window.signal_start)
        self.start_measurement_transition.setTargetState(self.s2)
        self.change_active_session_transition = ChangeActiveSessionTransition(self.s10.signal_yes)
        self.change_active_session_transition.setTargetState(self.s1)
        self.enter_annotated_events_transition = EnterAnnotatedEventsTransition(self.s3.signal_ok)
        self.enter_annotated_events_transition.setTargetState(self.s6)
        self.remove_annotated_events_transition = RemoveAnnotatedEventsTransition(self.s6.signal_close)
        self.remove_annotated_events_transition.setTargetState(self.s3)
        self.update_document_transition = UpdateDocumentTransition(self.s7.signal_yes)
        self.update_document_transition.setTargetState(self.s1)
        self.transition_map = {self.s1: {self.s2: self.start_measurement_transition,
                                         self.s3: self.main_window.signal_ok,
                                         self.s9: self.s1.signal_change_session,
                                         self.s11: self.main_window.signal_close},
                               self.s2: {self.s1: self.main_window.signal_stop},
                               self.s3: {self.s6: self.enter_annotated_events_transition},
                               self.s6: {self.s7: self.s6.signal_ok, self.s3: self.remove_annotated_events_transition},
                               self.s7: {self.s6: self.s7.signal_no, self.s1: self.update_document_transition},
                               self.s9: {self.s10: self.s9.signal_select, self.s1: self.s9.signal_cancel},
                               self.s10: {self.s9: self.s10.signal_no, self.s1: self.change_active_session_transition},
                               self.s11: {self.s1: self.s11.signal_no, self.s0: self.s11.signal_yes}}
        for source, targets in self.transition_map.items():
            for target, signal in targets.items():
                if type(signal) in (StartMeasurementTransition, ChangeActiveSessionTransition,
                                    EnterAnnotatedEventsTransition, RemoveAnnotatedEventsTransition,
                                    UpdateDocumentTransition):
                    source.addTransition(signal)
                else:
                    source.addTransition(signal, target)

    @property
    def active_session(self):
        return Session.get_instance()

    @active_session.setter
    def active_session(self, value: Session):
        Session.set_instance(value)

    @property
    def active_patient(self):
        return self.main_window.meta_widget.active_patient

    @active_patient.setter
    def active_patient(self, patient_id: str):
        self.main_window.meta_widget.active_patient = patient_id

    @property
    def active_distractor(self):
        return self.main_window.meta_widget.active_distractor

    @property
    def active_operator(self):
        return self.main_window.meta_widget.active_operator

    @property
    def producer_process(self):
        return self.main_window.producer_process

    @property
    def sensor(self):
        return self.main_window.sensor

    def in_state(self, state: QState) -> bool:
        """
        Determine if the state machine in a specified state.

        :param state:
        :return:
        """
        return state in self.configuration()

    def current_state(self) -> QState:
        """
        Return the current state the machine is in.

        :raises ValueError: If current state is not defined
        :return:
        """
        active_states = self.configuration()
        if len(active_states) != 1:
            raise ValueError(f'Current state not defined if {len(active_states)} states are active simultaneously')
        return list(active_states)[0]
