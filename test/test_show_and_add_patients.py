import pytest
from cranio.model import Patient, Document, Session
from cranio.producer import Sensor

patient_id = 'pytest-patient'


def test_add_patient_state_flow(machine):
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
    with machine.database.session_scope() as s:
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
    with machine.database.session_scope() as s:
        patients = s.query(Patient).filter(Patient.patient_id == patient_id).all()
        assert len(patients) == 1


@pytest.mark.parametrize('signal_name', ('signal_close', 'signal_ok'))
def test_s0_signals_to_transition_to_s1_and_patient_is_displayed_in_main_window(
    machine, signal_name
):
    Patient.add_new(patient_id=patient_id, database=machine.database)
    machine.s0.patient_widget.update_patients()
    machine.s0.select_patient(patient_id=patient_id)
    signal = getattr(machine.s0, signal_name)
    signal.emit()
    assert machine.in_state(machine.s1)
    assert machine.main_window.active_patient == machine.s1.active_patient == patient_id


def test_s0_selects_most_recently_used_patient_by_default(machine):
    with machine.database.session_scope() as s:
        session = Session()
        s.add(session)
        patient = Patient(patient_id=patient_id)
        s.add(patient)
        s.add(Sensor.sensor_info)
        s.flush()
        s.add(
            Document(
                patient_id=patient_id,
                session_id=session.session_id,
                sensor_serial_number=Sensor.sensor_info.sensor_serial_number,
                distractor_type=machine.distractor_type,
            )
        )
    machine.s0.update_patients()
    assert machine.s0.get_selected_patient_id() != patient_id
    machine.s0.select_most_recently_used_patient(database=machine.database)
    assert machine.s0.get_selected_patient_id() == patient_id
