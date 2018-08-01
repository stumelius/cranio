import pytest
import numpy as np
from sqlalchemy.exc import IntegrityError
from sqlalchemy.inspection import inspect
from cranio.core import generate_unique_id, utc_datetime
from cranio.utils import try_remove, get_logging_levels
from cranio.database import Patient, Session, Document, Measurement, Log, LogLevel, session_scope, export_schema_graph,\
    AnnotatedEvent, init_database, EventType


def assert_add_query_and_delete(rows, session, Table):
    primary_key_name = inspect(Table).primary_key[0].name
    # add rows
    for r in rows:
        session.add(r)
    # query and verify row insert
    results = session.query(Table).all()
    original_keys = [getattr(r, primary_key_name) for r in rows]
    queried_keys = [getattr(r, primary_key_name) for r in results]
    for key in original_keys:
        assert key in queried_keys
    # delete rows
    for r in rows:
        session.delete(r)
    # query and verify deletion
    results = session.query(Table).all()
    queried_keys = [getattr(r, primary_key_name) for r in results]
    for key in original_keys:
        assert key not in queried_keys


def test_create_query_and_delete_patient(database_fixture):
    with session_scope() as s:
        assert_add_query_and_delete([Patient(patient_id=generate_unique_id())], s, Patient)


def test_create_query_and_delete_session(database_fixture):
    with session_scope() as s:
        sessions = [Session()]
        assert_add_query_and_delete(sessions, s, Session)


def test_create_query_and_delete_document(database_patient_fixture):
    with session_scope() as s:
        d = Document(session_id=Session.get_instance().session_id, patient_id=Patient.get_instance().patient_id)
        assert_add_query_and_delete([d], s, Document)


def test_create_query_and_delete_measurement(database_document_fixture):
    with session_scope() as s:
        measurements = [Measurement(time_s=t, torque_Nm=np.random.rand(),
                                    document_id=Document.get_instance().document_id) for t in range(10)]
        assert_add_query_and_delete(measurements, s, Measurement)


def test_create_query_and_delete_log(database_fixture):
    with session_scope() as s:
        # create log for all logging levels
        logs = []
        for i, level in enumerate(get_logging_levels().keys()):
            log = Log(created_at=utc_datetime(), level=level, message=i, session_id=Session.get_instance().session_id,
                      trace='Empty', logger='test.logger')
            logs.append(log)
        assert_add_query_and_delete(logs, s, Log)


@pytest.mark.skip('FIXME: IntegrityError is raised after add')
def test_add_log_with_invalid_level(database_fixture):
    log = Log(created_at=utc_datetime(), level=1337, message='foo', session_id=Session.get_instance().session_id,
              trace='Empty', logger='test.logger')
    with session_scope() as s:
        with pytest.raises(IntegrityError):
            s.add(log)


@pytest.mark.skip('Requires graphviz')
def test_export_schema_graph():
    name = 'foo.png'
    export_schema_graph(name)
    try_remove(name)


def test_database_init_populate_lookup_tables(database_fixture):
    logging_levels = get_logging_levels()
    with session_scope() as s:
        # log levels
        levels = s.query(LogLevel).all()
        assert len(levels) == len(logging_levels)
        for log_level in s.query(LogLevel).all():
            assert log_level.level in logging_levels.keys()
            assert log_level.level_name in logging_levels.values()
        # event types
        event_types = s.query(EventType).all()
        targets = EventType.event_types()
        assert len(event_types) == len(targets)
        for real, target in zip(event_types, targets):
            assert real.event_type == target.event_type
            assert real.event_type_description == target.event_type_description


def test_create_query_and_delete_annotated_event(database_document_fixture):
    doc_id = Document.get_instance().document_id
    with session_scope() as s:
        events = [AnnotatedEvent(event_type=EventType.distraction_event_type().event_type, event_num=i, document_id=doc_id,
                                 annotation_done=False)
                  for i in range(10)]
        assert_add_query_and_delete(events, s, AnnotatedEvent)


@pytest.mark.skip('FIXME: IntegrityError is raised after add')
def test_annotated_event_foreign_key_constraint(database_fixture):
    with session_scope() as s:
        with pytest.raises(IntegrityError):
            s.add(AnnotatedEvent(event_type=EventType.distraction_event_type().event_type, event_num=1, document_id=1337))


def test_database_is_empty_after_reinitialization(database_fixture):
    with session_scope() as s:
        s.add(Log(session_id=Session.get_instance().session_id, created_at=utc_datetime(), logger='cranio',
                  level=0, message='foo'))
    # re-initialize
    init_database()
    with session_scope() as s:
        assert len(s.query(Session).all()) == 0


def test_get_time_series_related_to_document(database_document_fixture):
    # generate data and associate with document
    n = 100
    document = Document.get_instance()
    X = np.linspace(0, 1, n)
    Y = np.random.rand(n)
    with session_scope() as s:
        for x, y in zip(X, Y):
            s.add(Measurement(document_id=document.document_id, time_s=x, torque_Nm=y))
    x, y = document.get_related_time_series()
    np.testing.assert_array_almost_equal(x, X)
    np.testing.assert_array_almost_equal(y, Y)


def test_get_non_existing_time_series_related_to_document(database_document_fixture):
    document = Document.get_instance()
    x, y = document.get_related_time_series()
    assert len(x) == 0 and len(y) == 0
