import pytest
from cranio.app.widget import MetaDataWidget
from cranio.database import session_scope, Patient, Document


@pytest.fixture(scope='function')
def meta_data_widget():
    widget = MetaDataWidget()
    return widget


def test_meta_data_widget_add_patient(meta_data_widget):
    patient_id = 'foo'
    meta_data_widget.add_patient(patient_id)
    assert meta_data_widget.active_patient == patient_id


def test_meta_data_widget_update_patients_from_database(meta_data_widget, database_fixture):
    n = 10
    # add patients to database
    with session_scope() as s:
        for i in range(n):
            s.add(Patient(patient_id=i))
    # update widget
    meta_data_widget.update_patients_from_database()
    patients = meta_data_widget.patients()
    # verify patient count
    assert len(patients) == n
    # first inserted patient is active
    assert meta_data_widget.active_patient == patients[0]


'''
Test list for distractor edit

* (check) Toggle Patient Lock has no effect
* (check) Distractor identifier is 1 by default
* (check) Triggering "Up" button increases value by 1
* (check) Triggering "Down" button decreases value by 1
* (check) Boundary conditions: minimum value is 1, maximum value == 10
'''


def test_clicking_toggle_patient_lock_button_disables_patient_edit_only(meta_data_widget):
    patient_id = 'foo'
    meta_data_widget.add_patient(patient_id)
    # lock / disable patient edit
    meta_data_widget.toggle_patient_lock_button.clicked.emit(True)
    assert not meta_data_widget.patient_widget.isEnabled()
    # has no effect on distractor edit
    assert meta_data_widget.distractor_widget.isEnabled()
    # unlock / enable patient edit
    meta_data_widget.toggle_patient_lock_button.clicked.emit(True)
    assert meta_data_widget.patient_widget.isEnabled()
    assert meta_data_widget.distractor_widget.isEnabled()


def test_distractor_widget_value_is_one_by_default(meta_data_widget):
    assert meta_data_widget.distractor_widget.value == 1


def test_clicking_distractor_widget_up_increases_value_by_one(meta_data_widget):
    meta_data_widget.distractor_widget.step_up()
    assert meta_data_widget.distractor_widget.value == 2


def test_clicking_distractor_widget_down_decreases_value_by_one(meta_data_widget):
    meta_data_widget.distractor_widget.value = 2
    meta_data_widget.distractor_widget.step_down()
    assert meta_data_widget.distractor_widget.value == 1


def test_distractor_widget_down_has_no_effect_when_distractor_is_one(meta_data_widget):
    meta_data_widget.distractor_widget.step_down()
    assert meta_data_widget.distractor_widget.value == 1


def test_distractor_widget_up_has_no_effect_when_distractor_is_ten(meta_data_widget):
    meta_data_widget.distractor_widget.value = 10
    meta_data_widget.distractor_widget.step_up()
    assert meta_data_widget.distractor_widget.value == 10


def test_meta_data_widget_stores_active_operator_as_str(meta_data_widget):
    meta_data_widget.active_operator = 123
    assert meta_data_widget.active_operator == '123'





