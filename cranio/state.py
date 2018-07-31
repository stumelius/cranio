import logging
import multiprocessing as mp
from PyQt5.QtCore import QStateMachine, QState
from daqstore.store import DataStore
from cranio.app.window import MainWindow, RegionPlotWindow
from cranio.database import session_scope, Measurement, Session, Document
from cranio.core import utc_datetime


class MyStateMachine(QStateMachine):

    def __init__(self):
        super().__init__()
        # context
        DataStore.queue_cls = mp.Queue
        self.main_window = MainWindow()
        self.active_patient = self.main_window.meta_widget.active_patient
        self.active_distractor = self.main_window.meta_widget.active_distractor
        self.producer_process = self.main_window.producer_process
        self.document = None
        # states
        self.s1 = MyState('s1')
        self.s2 = MeasurementState()
        self.s3 = EventDetectionState()
        # transitions
        self.transition_map = {self.s1: {self.s2: self.main_window.signal_start, self.s3: self.main_window.signal_ok},
                               self.s2: {self.s1: self.main_window.signal_stop}}
        for source, targets in self.transition_map.items():
            for target, signal in targets.items():
                source.addTransition(signal, target)
        for s in (self.s1, self.s2, self.s3):
            self.addState(s)
        self.setInitialState(self.s1)


class MyState(QState):

    def __init__(self, name: str, parent=None):
        super().__init__(parent)
        self.name = name

    @property
    def main_window(self):
        return self.machine().main_window

    @property
    def document(self):
        return self.machine().document

    @document.setter
    def document(self, value: Document):
        self.machine().document = value

    def onEntry(self, event):
        logging.debug(f'Enter {self.name}')

    def onExit(self, state):
        logging.debug(f'Exit {self.name}')


class MeasurementState(MyState):

    def __init__(self, parent=None):
        super().__init__(name=type(self).__name__, parent=parent)

    def create_document(self):
        """
        Create new Document object.

        :return:
        :raises ValueError: if active patient is invalid
        """
        patient_id = self.machine().active_patient
        logging.debug(f'Active patient = {patient_id}')
        if not patient_id:
            raise ValueError(f'Invalid patient "{patient_id}"')
        return Document(session_id=Session.get_instance().session_id, patient_id=patient_id,
                        distractor_id=self.machine().active_distractor,
                        started_at=utc_datetime())

    def onEntry(self, event):
        super().onEntry(event)
        self.main_window.measurement_widget.update_timer.start(self.main_window.measurement_widget.update_interval * 1000)
        # create new document
        self.document = self.create_document()
        # insert document to database
        logging.debug(f'Enter document: {str(self.document.__dict__)}')
        with session_scope() as s:
            s.add(self.document)
        self.main_window.measurement_widget.producer_process.start()

    def onExit(self, event):
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
        self.dialog = None

    def onEntry(self, event):
        super().onEntry(event)
        # open region plot window
        self.dialog = RegionPlotWindow(document=self.document)
        self.dialog.show()