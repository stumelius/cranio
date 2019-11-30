import pytest
from cranio.app.widget import PatientWidget
from cranio.model import Patient
from cranio.utils import generate_unique_id


def test_patient_widget_updates_patients_from_database(database_fixture):
    pytest.helpers.add_patient(database_fixture)
    patient_widget = PatientWidget(database_fixture)
    assert patient_widget.patient_count() == 1
    patient_widget.update_patients()
    assert patient_widget.patient_count() == 1
    with database_fixture.session_scope() as s:
        s.add(Patient(patient_id=generate_unique_id()))
    assert patient_widget.patient_count() == 1
    patient_widget.update_patients()
    assert patient_widget.patient_count() == 2
