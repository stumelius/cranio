import pytest
from cranio.model import Patient, session_scope


def test_add_patient_state_flow(machine):
    patient_id = 'pytest-patient-state-flow'
    assert machine.in_state(machine.s1)
    # Trigger transition from s1 to s12 (ShowPatientsState)
    machine.s1.signal_show_patients.emit()
    assert machine.in_state(machine.s12)
    # Click Add (i.e,. trigger transition from s12 to s13 (AddPatientState))
    machine.s12.signal_add_patient.emit()
    assert machine.in_state(machine.s13)
    # Enter patient id and click Cancel (i.e., trigger transition from s13 back to s12)
    machine.s13.dialog.setTextValue(patient_id)
    machine.s13.signal_cancel.emit()
    assert machine.in_state(machine.s12)
    # Verify that patient was not added to database
    with session_scope(machine.database) as s:
        patients = s.query(Patient).filter(Patient.patient_id == patient_id).all()
        assert len(patients) == 0
    # Click Add (i.e,. trigger transition from s12 to s13 (AddPatientState))
    machine.s12.signal_add_patient.emit()
    assert machine.in_state(machine.s13)
    # Click Ok (i.e., trigger transition from s13 to s12)
    machine.s13.dialog.setTextValue(patient_id)
    machine.s13.signal_ok.emit()
    assert machine.in_state(machine.s12)
    # Verify that patient was added to database
    with session_scope(machine.database) as s:
        patients = s.query(Patient).filter(Patient.patient_id == patient_id).all()
        assert len(patients) == 1
    # Click X (i.e., trigger transition from s12 to s1)
    machine.s12.dialog.close()
    assert machine.in_state(machine.s1)
    # Initial state updates main window patient dropdown list on entry
    assert patient_id in machine.main_window.meta_widget.patients()
