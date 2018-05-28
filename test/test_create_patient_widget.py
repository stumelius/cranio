import pytest
from cranio.app.dialogs import CreatePatientWidget
from sqlalchemy import exists
from cranio.database import Patient, session_scope, IntegrityError


def patient_exists(patient_id: str) -> bool:
    ''' Check if a given patient id already exists in the database '''
    with session_scope() as session:
        return session.query(exists().where(Patient.id == patient_id)).scalar()


def test_add_patient():
    widget = CreatePatientWidget()
    for i, name in enumerate(('foo', 'bar', 'baz')):
        widget.add_patient(name)
        assert widget.patient_count() == i+1


def test_add_patient_already_exists():
    widget = CreatePatientWidget()
    widget.add_patient('foo bar')
    with pytest.raises(IntegrityError):
        widget.add_patient('foo bar')
