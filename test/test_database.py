import pytest
import numpy as np
from datetime import datetime
from cranio.core import generate_unique_id
from cranio.database import Patient, Session, Document, Measurement, Log, LogLevel, session_scope


def assert_add_query_and_delete(rows, session, Table):
    # add rows
    for r in rows:
        session.add(r)
    # query and verify row insert
    results = session.query(Table).all()
    assert len(results) == len(rows)
    for original, queried in zip(rows, results):
        assert original.id == queried.id
    # delete rows
    for r in rows:
        session.delete(r)
    assert len(session.query(Table).all()) == 0


@pytest.fixture
def patient():
    p = Patient(id=generate_unique_id())
    return p


@pytest.fixture
def session(patient):
    s = Session(id=generate_unique_id(), patient_id=patient.id)
    return s


@pytest.fixture
def document(session):
    d = Document(id=generate_unique_id(), session_id=session.id)
    return d


def test_create_query_and_delete_patient(patient):
    with session_scope() as sql_session:
        patients = [patient]
        assert_add_query_and_delete(patients, sql_session, Patient)


def test_create_query_and_delete_session(patient):
    with session_scope() as sql_session:
        sql_session.add(patient)
        s = Session(patient_id=patient.id)
        sessions = [s]
        assert_add_query_and_delete(sessions, sql_session, Session)
        assert len(sql_session.query(Patient).all()) == 1


def test_create_query_and_delete_document(patient):
    with session_scope() as sql_session:
        # first create session to get session_id
        session = Session(patient_id=patient.id)
        sql_session.add(session)
        # flush to realize session_id
        sql_session.flush()
        assert session.id is not None
        sql_session.add(patient)
        d = Document(session_id=session.id)
        assert_add_query_and_delete([d], sql_session, Document)


def test_create_query_and_delete_measurement(document):
    with session_scope() as sql_session:
        measurements = [Measurement(time_s=t, torque_Nm=np.random.rand(), document_id=document.id) for t in range(10)]
        assert_add_query_and_delete(measurements, sql_session, Measurement)


def test_create_query_and_delete_log():
    with session_scope() as sql_session:
        logs = [Log(datetime=datetime.utcnow(), level=np.random.choice(LogLevel), message=i) for i in range(10)]
        assert_add_query_and_delete(logs, sql_session, Log)
        # sql_session.query(Log).filter_by(level=LogLevel.INFO).all()
