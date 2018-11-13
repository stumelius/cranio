import pytest
from cranio.app.widget import PatientWidget
from sqlalchemy import exists
from sqlalchemy.exc import IntegrityError
from cranio.model import Patient, session_scope, init_database


def patient_exists(patient_id: str) -> bool:
    ''' Check if a given patient id already exists in the database '''
    init_database()
    with session_scope() as session:
        return session.query(exists().where(Patient.id == patient_id)).scalar()


def test_add_patient():
    init_database()
    widget = PatientWidget()
    for i, name in enumerate(('foo', 'bar', 'baz')):
        widget.add_patient(name)
        assert widget.patient_count() == i+1


def test_add_patient_already_exists():
    init_database()
    widget = PatientWidget()
    widget.add_patient('foo bar')
    with pytest.raises(IntegrityError):
        widget.add_patient('foo bar')


def test_add_patient_empty_string():
    init_database()
    widget = PatientWidget()
    with pytest.raises(IntegrityError):
        widget.add_patient('')
