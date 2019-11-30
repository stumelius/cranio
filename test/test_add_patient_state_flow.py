import pytest
from cranio.model import Patient, session_scope


def test_add_patient_state_flow(machine):
    patient_id = 'pytest-patient-state-flow'
    # Start in ShortPatientsState
    assert machine.in_state(machine.s0)
    # Click Add (i.e,. trigger transition from s0 to s0_1 (AddPatientState))
    machine.s0.signal_add_patient.emit()
    assert machine.in_state(machine.s0_1)
    # Enter patient id and click Cancel (i.e., trigger transition from s0_1 back to s0)
    machine.s0_1.dialog.setTextValue(patient_id)
    machine.s0_1.signal_cancel.emit()
    assert machine.in_state(machine.s0)
    # Verify that patient was not added to database
    with session_scope(machine.database) as s:
        patients = s.query(Patient).filter(Patient.patient_id == patient_id).all()
        assert len(patients) == 0
    # Click Add (i.e,. trigger transition from s0 to s0_1 (AddPatientState))
    machine.s0.signal_add_patient.emit()
    assert machine.in_state(machine.s0_1)
    # Click Ok (i.e., trigger transition from s0_1 to s0)
    machine.s0_1.dialog.setTextValue(patient_id)
    machine.s0_1.signal_ok.emit()
    assert machine.in_state(machine.s0)
    # Verify that patient was added to database
    with session_scope(machine.database) as s:
        patients = s.query(Patient).filter(Patient.patient_id == patient_id).all()
        assert len(patients) == 1


@pytest.mark.parametrize('signal_name', ('signal_close', 'signal_ok'))
def test_s0_signals_to_transition_to_s1_and_patient_is_displayed_in_main_window(
    machine, signal_name
):
    patient_id = 'pytest-patient-state-flow'
    Patient.add_new(patient_id=patient_id, database=machine.database)
    machine.s0.patient_widget.update_patients()
    # Select patient
    index = machine.s0.patient_widget.select_widget.findText(patient_id)
    assert index != -1
    machine.s0.patient_widget.select_widget.setCurrentIndex(index)
    signal = getattr(machine.s0, signal_name)
    signal.emit()
    assert machine.in_state(machine.s1)
    assert machine.main_window.active_patient == machine.s1.active_patient == patient_id
