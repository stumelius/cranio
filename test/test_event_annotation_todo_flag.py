'''
List of tests:
* (check) Annotated event can be flagged as undone
* Checking the "Done" checkbox sets Done = True
* Unchecking the "Done" checkbox sets Done = False
'''

from cranio.database import AnnotatedEvent, Document, DISTRACTION_EVENT_TYPE_OBJECT


def test_annotated_event_can_be_flagged_as_undone(database_document_fixture):
    document_id = Document.get_instance()
    event_type = DISTRACTION_EVENT_TYPE_OBJECT.event_type
    annotated_event = AnnotatedEvent(event_num=1, event_type=event_type, document_id=document_id, annotation_done=False)
    assert not annotated_event.annotation_done

