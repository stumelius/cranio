import logging
from copy import copy
from typing import List
from PyQt5.QtCore import QStateMachine, QState, QEvent, pyqtSignal, QSignalTransition
from PyQt5.QtWidgets import QMessageBox
from cranio.app.window import MainWindow, RegionPlotWindow, NotesWindow
from cranio.database import session_scope, Measurement, Session, Document, AnnotatedEvent, SensorInfo, DistractorType
from cranio.core import utc_datetime


class MyState(QState):
    def __init__(self, name: str, parent=None):
        super().__init__(parent)
        self.name = name

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
        logging.debug(f'Enter {self.name}')

    def onExit(self, event: QEvent):
        logging.debug(f'Exit {self.name}')


class InitialState(MyState):
    def __init__(self, parent=None):
        super().__init__(name=type(self).__name__, parent=parent)

    def onEntry(self, event: QEvent):
        super().onEntry(event)
        self.main_window.show()


class MeasurementState(MyState):
    def __init__(self, parent=None):
        super().__init__(name=type(self).__name__, parent=parent)

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
        # create new document
        self.document = self.create_document()
        self.main_window.measurement_widget.update_timer.start(self.main_window.measurement_widget.update_interval*1000)
        # insert sensor info and document to database
        sensor.enter_info_to_database()
        with session_scope() as s:
            logging.debug(f'Enter document: {str(self.document)}')
            s.add(self.document)
        self.main_window.measurement_widget.producer_process.start()

    def onExit(self, event: QEvent):
        super().onExit(event)
        # pause producer process and stop timer
        if self.main_window.measurement_widget.producer_process is None:
            return
        self.main_window.measurement_widget.producer_process.pause()
        self.main_window.measurement_widget.update_timer.stop()
        # enter data to database
        plot_widgets = self.main_window.measurement_widget.multiplot_widget.plot_widgets
        if len(plot_widgets) > 1:
            raise ValueError('Only single plots are supported')
        elif len(plot_widgets) == 0:
            logging.debug('No data to enter')
            # no data to enter
            return
        plot_widget = self.main_window.measurement_widget.multiplot_widget.plot_widgets[0]
        measurements = []
        with session_scope() as s:
            for x, y in zip(plot_widget.x, plot_widget.y):
                m = Measurement(document_id=self.document.document_id, time_s=x, torque_Nm=y)
                measurements.append(m)
                s.add(m)
        logging.debug(f'Entered {len(measurements)} measurements to the database')


class EventDetectionState(MyState):

    def __init__(self, parent=None):
        super().__init__(name=type(self).__name__, parent=parent)
        self.dialog = RegionPlotWindow()
        # signals
        self.signal_ok = self.dialog.ok_button.clicked

    def onEntry(self, event: QEvent):
        """
        Open a RegionPlotWindow and plot context document data.

        :param event:
        :return:
        """
        super().onEntry(event)
        self.dialog.plot(*self.document.get_related_time_series())
        # clear existing regions
        self.dialog.clear_regions()
        # add as many regions as there are turns in one full turn
        sensor_info = self.document.get_related_sensor_info()
        self.dialog.set_add_count(int(sensor_info.turns_in_full_turn))
        self.dialog.add_button_clicked()
        self.dialog.show()

    def onExit(self, event: QEvent):
        super().onExit(event)
        # assign annotated events and link to document
        logging.debug('Assign annotated events and link to document')
        self.annotated_events = self.dialog.get_annotated_events()
        for e in self.annotated_events:
            e.document_id = self.document.document_id
        for event in self.annotated_events:
            logging.debug(str(event))
        self.dialog.close()

    def region_count(self):
        return self.dialog.region_count()


class AreYouSureState(MyState):

    def __init__(self, text_template: str, parent=None):
        """

        :param text: Text shown in the dialog
        :param parent:
        """
        super().__init__(name=type(self).__name__, parent=parent)
        self.template = text_template
        self.dialog = QMessageBox()
        self.yes_button = self.dialog.addButton('Yes', QMessageBox.YesRole)
        self.no_button = self.dialog.addButton('No', QMessageBox.NoRole)
        self.dialog.setIcon(QMessageBox.Question)
        self.dialog.setWindowTitle('Are you sure?')
        # signals
        self.signal_yes = self.yes_button.clicked
        self.signal_no = self.no_button.clicked

    def namespace(self) -> dict:
        """ Return template namespace. """
        try:
            region_count = len(self.annotated_events)
        except AttributeError:
            # object has no attribute 'annotated_events'
            region_count = None
        return {'region_count': region_count}

    def onEntry(self, event: QEvent):
        super().onEntry(event)
        self.dialog.setText(self.template.format(**self.namespace()))
        self.dialog.open()

    def onExit(self, event: QEvent):
        super().onExit(event)
        self.dialog.close()


class EnterAnnotatedEventsState(MyState):
    signal_finished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(name=type(self).__name__, parent=parent)

    def onEntry(self, event: QEvent):
        super().onEntry(event)
        if not self.annotated_events:
            raise ValueError('No annotated events to enter')
        logging.debug('Enter annotated events to database')
        with session_scope() as s:
            for e in self.annotated_events:
                s.add(e)
                logging.debug(str(e))
        self.signal_finished.emit()


class NoteState(MyState):
    def __init__(self, parent=None):
        super().__init__(name=type(self).__name__, parent=parent)
        self.dialog = NotesWindow()
        # signals
        self.signal_ok = self.dialog.ok_button.clicked

    def onEntry(self, event: QEvent):
        super().onEntry(event)
        # set default full turn count
        event_count = len(self.document.get_related_events())
        with session_scope() as s:
            sensor_info = s.query(SensorInfo).\
                filter(SensorInfo.sensor_serial_number == self.document.sensor_serial_number).first()
        self.full_turn_count = event_count / float(sensor_info.turns_in_full_turn)
        self.dialog.open()

    def onExit(self, event: QEvent):
        super().onExit(event)
        # update document and close window
        self.document.notes = self.dialog.notes
        self.document.full_turn_count = self.dialog.full_turn_count
        self.dialog.close()

    @property
    def full_turn_count(self):
        return self.dialog.full_turn_count

    @full_turn_count.setter
    def full_turn_count(self, value):
        self.dialog.full_turn_count = value




class UpdateDocumentState(MyState):
    signal_finished = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(name=type(self).__name__, parent=parent)

    def onEntry(self, event: QEvent):
        super().onEntry(event)
        logging.debug('Update document in database')
        with session_scope() as s:
            document = s.query(Document).filter(Document.document_id == self.document.document_id).first()
            document.notes = self.document.notes
            document.full_turn_count = self.document.full_turn_count
            logging.debug(str(document))
        self.signal_finished.emit()


class StartMeasurementTransition(QSignalTransition):

    def __init__(self, signal: pyqtSignal, source_state: QState=None):
        """

        :param source_state:
        """
        super().__init__(signal, source_state)

    def eventTest(self, event: QEvent) -> bool:
        if not super().eventTest(event):
            return False
        # invalid patient
        if not self.sourceState().machine().active_patient:
            logging.error(f'Invalid patient "{self.sourceState().machine().active_patient}"')
            return False
        # no sensor connected
        if len(self.sourceState().machine().producer_process.sensors) == 0:
            logging.error('No sensors connected')
            return False
        # too many sensors connected
        if len(self.sourceState().machine().producer_process.sensors) > 1:
            logging.error('More than one sensor connected')
            return False
        return True


class MyStateMachine(QStateMachine):

    def __init__(self):
        super().__init__()
        # context
        self.main_window = MainWindow()
        self.document = None
        self.annotated_events = None
        # states
        self.s1 = InitialState()
        self.s2 = MeasurementState()
        self.s3 = EventDetectionState()
        self.s4 = AreYouSureState('You have selected {region_count} regions. '
                                  'Are you sure you want to continue?')
        self.s5 = EnterAnnotatedEventsState()
        self.s6 = NoteState()
        self.s7 = AreYouSureState('Are you sure you want to continue?')
        self.s8 = UpdateDocumentState()
        # transitions
        self.start_measurement_transition = StartMeasurementTransition(self.main_window.signal_start)
        self.start_measurement_transition.setTargetState(self.s2)
        self.transition_map = {self.s1: {self.s2: self.start_measurement_transition, self.s3: self.main_window.signal_ok},
                               self.s2: {self.s1: self.main_window.signal_stop},
                               self.s3: {self.s4: self.s3.signal_ok},
                               self.s4: {self.s3: self.s4.signal_no, self.s5: self.s4.signal_yes},
                               self.s5: {self.s6: self.s5.signal_finished},
                               self.s6: {self.s7: self.s6.signal_ok},
                               self.s7: {self.s6: self.s7.signal_no, self.s8: self.s7.signal_yes},
                               self.s8: {self.s1: self.s8.signal_finished}}
        for source, targets in self.transition_map.items():
            for target, signal in targets.items():
                if type(signal) == StartMeasurementTransition:
                    source.addTransition(signal)
                else:
                    source.addTransition(signal, target)
        for s in (self.s1, self.s2, self.s3, self.s4, self.s5, self.s6, self.s7, self.s8):
            self.addState(s)
        self.setInitialState(self.s1)

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
        if len(self.producer_process.sensors) != 1:
            raise ValueError('Too many sensors connected')
        return self.producer_process.sensors[0]

    def in_state(self, state: QState) -> bool:
        """
        Determine if the state machine in a specified state.

        :param state:
        :return:
        """
        return state in self.configuration()
