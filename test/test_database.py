import pytest
import numpy as np
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy.inspection import inspect
from cranio.core import generate_unique_id, utc_datetime
from cranio.utils import try_remove, get_logging_levels
from cranio.database import (Patient, Session, Document, Measurement, Log, LogLevel, session_scope,
                             export_schema_graph, EVENT_TYPE_DISTRACTION, AnnotatedEvent, init_database)


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
        d = Document(session_id=Session.instance_id, patient_id=Patient.instance_id)
        assert_add_query_and_delete([d], s, Document)


def test_create_query_and_delete_measurement(database_document_fixture):
    with session_scope() as s:
        measurements = [Measurement(time_s=t, torque_Nm=np.random.rand(),
                                    document_id=Document.instance_id) for t in range(10)]
        assert_add_query_and_delete(measurements, s, Measurement)


def test_create_query_and_delete_log(database_fixture):
    with session_scope() as s:
        # create log for all logging levels
        logs = []
        for i, level in enumerate(get_logging_levels().keys()):
            log = Log(created_at=utc_datetime(), level=level, message=i, session_id=Session.get_instance(),
                      trace='Empty', logger='test.logger')
            logs.append(log)
        assert_add_query_and_delete(logs, s, Log)


@pytest.mark.skip('FIXME: IntegrityError is raised after add')
def test_add_log_with_invalid_level(database_fixture):
    log = Log(created_at=utc_datetime(), level=1337, message='foo', session_id=Session.get_instance(),
              trace='Empty', logger='test.logger')
    with session_scope() as s:
        with pytest.raises(IntegrityError):
            s.add(log)


@pytest.mark.skip('Requires graphviz')
def test_export_schema_graph():
    name = 'foo.png'
    export_schema_graph(name)
    try_remove(name)


def test_database_init_populate_lookup_table(database_fixture):
    logging_levels = get_logging_levels()
    with session_scope() as s:
        levels = s.query(LogLevel).all()
        assert len(levels) == len(logging_levels)
        for log_level in s.query(LogLevel).all():
            assert log_level.level in logging_levels.keys()
            assert log_level.level_name in logging_levels.values()


def test_create_query_and_delete_annotated_event(database_document_fixture):
    doc_id = Document.instance_id
    with session_scope() as s:
        events = [AnnotatedEvent(event_type=EVENT_TYPE_DISTRACTION.event_type, event_num=i, document_id=doc_id)
                  for i in range(10)]
        assert_add_query_and_delete(events, s, AnnotatedEvent)


@pytest.mark.skip('FIXME: IntegrityError is raised after add')
def test_annotated_event_foreign_key_constraint(database_fixture):
    with session_scope() as s:
        with pytest.raises(IntegrityError):
            s.add(AnnotatedEvent(event_type=EVENT_TYPE_DISTRACTION.event_type, event_num=1, document_id=1337))


def test_database_is_empty_after_reinitialization(database_fixture):
    with session_scope() as s:
        s.add(Log(session_id=Session.get_instance(), created_at=utc_datetime(), logger='cranio', level=0, message='foo'))
    # re-initialize
    init_database()
    with session_scope() as s:
        assert len(s.query(Session).all()) == 0

