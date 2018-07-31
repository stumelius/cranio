import pytest
import time
from cranio.app import app
from cranio.state import MyStateMachine
from cranio.database import Patient, Document, Measurement, session_scope
from cranio.utils import attach_excepthook


@pytest.fixture
def machine(database_patient_fixture):
    state_machine = MyStateMachine()
    # set active patient
    state_machine.active_patient = Patient.get_instance().patient_id
    state_machine.start()
    app.processEvents()
    yield state_machine
    # kill producer
    if state_machine.producer_process.is_alive():
        state_machine.producer_process.join()
    state_machine.stop()


def test_start_measurement_inserts_document_to_database(machine):
    # start measurement
    machine.transition_map[machine.s1][machine.s2].emit()
    app.processEvents()
    assert machine.document is not None
    with session_scope() as s:
        document = s.query(Document).first()
        assert document.document_id == machine.document.document_id


def test_stop_measurement_pauses_producer_and_inserts_measurements_to_database(machine):
    # attach dummy sensor
    machine.main_window.connect_dummy_sensor_action.triggered.emit()
    app.processEvents()
    # start measurement for 2 seconds
    machine.transition_map[machine.s1][machine.s2].emit()
    time.sleep(2)
    app.processEvents()
    # stop measurement
    machine.transition_map[machine.s2][machine.s1].emit()
    app.processEvents()
    assert machine.producer_process.is_alive()
    with session_scope() as s:
        measurements = s.query(Measurement).filter(Measurement.document_id == machine.document.document_id).all()
        assert len(measurements) > 0


def test_main_window_ok_triggers_event_detection(machine):
    attach_excepthook()
    # TODO: create document and insert data
    document = machine.s2.create_document()
    machine.transition_map[machine.s1][machine.s3].emit()




