import pytest
import numpy as np
import time
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy.inspection import inspect
from cranio.core import generate_unique_id
from cranio.utils import try_remove, get_logging_levels
from cranio.database import (Patient, Session, Document, Measurement, Log, LogLevel, session_scope,
                             export_schema_graph, init_database)


@pytest.fixture()
def init():
    init_database()
    # initialize session, patient and document
    Session.init()
    Patient.init(patient_id=generate_unique_id())
    Document.init(patient_id=Patient.instance_id)
    yield
    # reset
    for cls in (Session, Patient, Document):
        cls.instance_id = None
    # clear tables
    with session_scope() as s:
        s.query(Document).delete()
        s.query(Patient).delete()
        s.query(Session).delete()


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


def test_create_query_and_delete_patient(init):
    with session_scope() as s:
        assert_add_query_and_delete([Patient(patient_id=generate_unique_id())], s, Patient)


def test_create_query_and_delete_session(init):
    with session_scope() as s:
        sessions = [Session()]
        assert_add_query_and_delete(sessions, s, Session)


def test_create_query_and_delete_document(init):
    with session_scope() as s:
        d = Document(session_id=Session.instance_id, patient_id=Patient.instance_id)
        assert_add_query_and_delete([d], s, Document)


def test_create_query_and_delete_measurement(init):
    with session_scope() as s:
        measurements = [Measurement(time_s=t, torque_Nm=np.random.rand(),
                                    document_id=Document.instance_id) for t in range(10)]
        assert_add_query_and_delete(measurements, s, Measurement)


def test_create_query_and_delete_log(init):
    with session_scope() as s:
        # create log for all logging levels
        logs = []
        for i, level in enumerate(get_logging_levels().keys()):
            log = Log(created_at=datetime.utcnow(), level=level, message=i, document_id=Document.instance_id,
                      trace='Empty', logger='test.logger')
            logs.append(log)
        assert_add_query_and_delete(logs, s, Log)


@pytest.mark.skip('FIXME: IntegrityError is raised after add')
def test_add_log_with_invalid_level(init):
    log = Log(created_at=datetime.utcnow(), level=1337, message='foo', document_id=Document.instance_id,
              trace='Empty', logger='test.logger')
    with session_scope() as s:
        with pytest.raises(IntegrityError):
            s.add(log)


@pytest.mark.skip('Requires graphviz')
def test_export_schema_graph():
    name = 'foo.png'
    export_schema_graph(name)
    try_remove(name)


def test_database_init_populate_lookup_table(init):
    logging_levels = get_logging_levels()
    with session_scope() as s:
        levels = s.query(LogLevel).all()
        assert len(levels) == len(logging_levels)
        for log_level in s.query(LogLevel).all():
            assert log_level.level in logging_levels.keys()
            assert log_level.level_name in logging_levels.values()


def test_init_session():
    assert Session.instance_id is None
    Session.init()
    assert Session.instance_id is not None


def test_init_document():
    patient_id = 'foo'
    assert Document.instance_id is None
    # no patient initialized
    with pytest.raises(ValueError):
        Document.init()
    # add patient and initialize document
    with session_scope() as s:
        p = Patient(patient_id=patient_id)
        s.add(p)
    Document.init(patient_id=patient_id)
    assert Document.instance_id is not None
