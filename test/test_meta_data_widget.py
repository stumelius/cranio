import pytest
from cranio.app.dialogs import MetaDataWidget
from cranio.database import session_scope, Patient


@pytest.fixture(scope='function')
def session_meta_widget():
    widget = MetaDataWidget()
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


'''
Test list for distractor edit

* (check) Toggle Patient Lock has no effect
* (check) Distractor identifier is 1 by default
* (check) Triggering "Up" button increases value by 1
* (check) Triggering "Down" button decreases value by 1
* (check) Boundary conditions: minimum value is 1, maximum value == 10
'''


def test_clicking_toggle_patient_lock_button_disables_patient_edit_only(session_meta_widget):
    patient_id = 'foo'
    session_meta_widget.add_patient(patient_id)
    # lock / disable patient edit
    session_meta_widget.toggle_patient_lock_button.clicked.emit(True)
    assert not session_meta_widget.patient_widget.isEnabled()
    # has no effect on distractor edit
    assert session_meta_widget.distractor_widget.isEnabled()
    # unlock / enable patient edit
    session_meta_widget.toggle_patient_lock_button.clicked.emit(True)
    assert session_meta_widget.patient_widget.isEnabled()
    assert session_meta_widget.distractor_widget.isEnabled()


def test_distractor_widget_value_is_one_by_default(session_meta_widget):
    assert session_meta_widget.distractor_widget.value == 1


def test_clicking_distractor_widget_up_increases_value_by_one(session_meta_widget):
    session_meta_widget.distractor_widget.step_up()
    assert session_meta_widget.distractor_widget.value == 2


def test_clicking_distractor_widget_down_decreases_value_by_one(session_meta_widget):
    session_meta_widget.distractor_widget.value = 2
    session_meta_widget.distractor_widget.step_down()
    assert session_meta_widget.distractor_widget.value == 1


def test_distractor_widget_down_has_no_effect_when_distractor_is_one(session_meta_widget):
    session_meta_widget.distractor_widget.step_down()
    assert session_meta_widget.distractor_widget.value == 1


def test_distractor_widget_up_has_no_effect_when_distractor_is_ten(session_meta_widget):
    session_meta_widget.distractor_widget.value = 10
    session_meta_widget.distractor_widget.step_up()
    assert session_meta_widget.distractor_widget.value == 10





