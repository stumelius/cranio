from PyQt5.QtCore import QEvent, QSignalTransition
from cranio.database import session_scope, Session, Document, AnnotatedEvent
from cranio.utils import logger


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