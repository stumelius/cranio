import pytest
from cranio.app.widget import MetaDataWidget
from cranio.model import session_scope, Patient


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


def test_clicking_toggle_patient_lock_button_disables_patient_edit_only(meta_data_widget):
    patient_id = 'foo'
    meta_data_widget.add_patient(patient_id)
    # lock / disable patient edit
    meta_data_widget.toggle_patient_lock_button.clicked.emit(True)
    assert not meta_data_widget.patient_widget.isEnabled()
    # unlock / enable patient edit
    meta_data_widget.toggle_patient_lock_button.clicked.emit(True)
    assert meta_data_widget.patient_widget.isEnabled()


def test_meta_data_widget_stores_active_operator_as_str(meta_data_widget):
    meta_data_widget.active_operator = 123
    assert meta_data_widget.active_operator == '123'
