"""
System state transitions.
"""
from PyQt5.QtCore import QEvent, QSignalTransition
from cranio.model import session_scope, Session, Document, AnnotatedEvent
from cranio.utils import logger
from cranio.state import StateMachineContextMixin


class SignalTransition(QSignalTransition, StateMachineContextMixin):
    pass


class StartMeasurementTransition(SignalTransition):
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


class ChangeActiveSessionTransition(SignalTransition):
    def onTransition(self, event: QEvent):
        super().onTransition(event)
        # Change active session
        session_id = self.machine().s9.active_session_id()
        logger.debug(f'[{type(self).__name__}] Change active session to {session_id}')
        with session_scope(self.database) as s:
            session = s.query(Session).filter(Session.session_id == session_id).first()
        self.machine().active_session = session


class EnterAnnotatedEventsTransition(SignalTransition):
    def onTransition(self, event: QEvent):
        super().onTransition(event)
        # Assign annotated events and link to document
        logger.debug('Assign annotated events and link to document')
        self.annotated_events = self.sourceState().get_annotated_events()
        for e in self.annotated_events:
            e.document_id = self.document.document_id
        logger.debug('Enter annotated events to database')
        for e in self.annotated_events:
            self.database.insert(e)
            logger.debug(str(e))


class RemoveAnnotatedEventsTransition(SignalTransition):
    def onTransition(self, event: QEvent):
        super().onTransition(event)
        with session_scope(self.database) as s:
            for e in self.machine().annotated_events:
                logger.debug(f'Remove {str(e)} from database')
                s.query(AnnotatedEvent).filter(AnnotatedEvent.document_id == e.document_id).\
                    filter(AnnotatedEvent.event_type == e.event_type).\
                    filter(AnnotatedEvent.event_num == e.event_num).delete()


class UpdateDocumentTransition(SignalTransition):
    def onTransition(self, event: QEvent):
        super().onTransition(event)
        logger.debug('Update document in database')
        with session_scope(self.database) as s:
            document = s.query(Document).filter(Document.document_id == self.document.document_id).first()
            document.notes = self.document.notes
            document.full_turn_count = self.document.full_turn_count
            logger.debug(str(document))
