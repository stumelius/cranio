import pytest
from cranio.app.dialogs import SessionMetaWidget
from cranio.database import session_scope, Patient


@pytest.fixture(scope='function')
def session_meta_widget():
    widget = SessionMetaWidget()
    return widget


def test_session_meta_widget_add_patient(session_meta_widget):
    patient_id = 'foo'
    session_meta_widget.add_patient(patient_id)
    assert session_meta_widget.active_patient == patient_id


def test_session_meta_widget_update_patients_from_database(session_meta_widget, database_document_fixture):
    n = 10
    # add patients to database
    with session_scope() as s:
        for i in range(n):
            s.add(Patient(patient_id=i))
    # update widget
    session_meta_widget.update_patients_from_database()
    patients = session_meta_widget.patients()
    # verify patient count
    # NOTE: database_document_fixture initializes a patient record by default. therefore, total patients is n + 1
    assert len(patients) == n + 1
    # first inserted patient is active
    assert session_meta_widget.active_patient == patients[0]


def test_clicking_toggle_patient_lock_button_disables_patient_edit_only(session_meta_widget):
    patient_id = 'foo'
    session_meta_widget.add_patient(patient_id)
    # lock / disable patient edit
    session_meta_widget.toggle_patient_lock_button.clicked.emit(True)
    assert not session_meta_widget.patient_widget.isEnabled()
    # unlock / enable patient edit
    session_meta_widget.toggle_patient_lock_button.clicked.emit(True)
    assert session_meta_widget.patient_widget.isEnabled()




