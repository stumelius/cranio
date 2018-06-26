import pytest
from cranio.app.dialogs import SessionMetaWidget
from cranio.database import init_database, session_scope, Patient


@pytest.fixture
def session_meta_widget():
    widget = SessionMetaWidget()
    yield widget


def test_session_meta_widget_add_patient(session_meta_widget):
    patient_id = 'foo'
    session_meta_widget.add_patient(patient_id)
    assert session_meta_widget.active_patient == patient_id


def test_session_meta_widget_update_patients_from_database(session_meta_widget):
    n = 10
    # add patients to database
    init_database()
    with session_scope() as s:
        for i in range(n):
            s.add(Patient(patient_id=i))
    # update widget
    session_meta_widget.update_patients_from_database()
    patients = session_meta_widget.patients()
    # verify patient count
    assert len(patients) == n
    # verify active patient
    assert session_meta_widget.active_patient == '0'

