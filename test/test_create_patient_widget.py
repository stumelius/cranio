import pytest
from cranio.app.dialogs import CreatePatientWidget
from sqlalchemy import exists
from cranio.database import Patient, session_scope, IntegrityError, init_database


def patient_exists(patient_id: str) -> bool:
    ''' Check if a given patient id already exists in the database '''
    init_database()
    with session_scope() as session:
        return session.query(exists().where(Patient.id == patient_id)).scalar()


def test_add_patient():
    init_database()
    widget = CreatePatientWidget()
    for i, name in enumerate(('foo', 'bar', 'baz')):
        widget.add_patient(name)
        assert widget.patient_count() == i+1


def test_add_patient_already_exists():
    init_database()
    widget = CreatePatientWidget()
    widget.add_patient('foo bar')
    with pytest.raises(IntegrityError):
        widget.add_patient('foo bar')
