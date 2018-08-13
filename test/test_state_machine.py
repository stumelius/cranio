import pytest
import time
import logging
from PyQt5.QtCore import QEvent
from cranio.app import app
from cranio.state import MyStateMachine, AreYouSureState
from cranio.database import Patient, Document, Measurement, session_scope, insert_time_series_to_database, \
    AnnotatedEvent, Log, SensorInfo
from cranio.producer import plug_dummy_sensor
from cranio.utils import attach_excepthook

wait_sec = 0.5
attach_excepthook()


@pytest.fixture(scope='function')
def machine(database_patient_fixture):
    state_machine = MyStateMachine()
    # connect dummy sensor
    plug_dummy_sensor(state_machine.producer_process)
    # set active patient
    state_machine.active_patient = Patient.get_instance().patient_id
    state_machine.start()
    app.processEvents()
    yield state_machine
    # kill producer
    if state_machine.producer_process.is_alive():
        state_machine.producer_process.join()
    state_machine.stop()


@pytest.fixture
def machine_without_patient(database_fixture):
    state_machine = MyStateMachine()
    state_machine.start()
    app.processEvents()
    yield state_machine
    # kill producer
    if state_machine.producer_process.is_alive():
        state_machine.producer_process.join()
    state_machine.stop()


def caught_exceptions():
    """ Return caught exceptions from log database. """
    with session_scope() as s:
        errors = s.query(Log).filter(Log.level == logging.ERROR).all()
    return errors


def test_start_measurement_inserts_document_and_sensor_info_to_database(machine):
    # start measurement
    machine.main_window.measurement_widget.start_button.clicked.emit()
    app.processEvents()
    assert machine.document is not None
    with session_scope() as s:
        document = s.query(Document).first()
        assert document.document_id == machine.document.document_id
        # verify patient, distractor and operator
        assert document.patient_id == machine.active_patient
        assert document.distractor_number == machine.active_distractor
        assert document.operator == machine.active_operator
        assert document.sensor_serial_number
        sensor_info = s.query(SensorInfo).filter(SensorInfo.sensor_serial_number == document.sensor_serial_number).all()
        assert len(sensor_info) == 1


def test_stop_measurement_pauses_producer_and_inserts_measurements_to_database(machine):
    # start measurement for 2 seconds
    machine.main_window.measurement_widget.start_button.clicked.emit()
    time.sleep(2)
    app.processEvents()
    # stop measurement
    machine.main_window.measurement_widget.stop_button.clicked.emit()
    app.processEvents()
    assert machine.producer_process.is_alive()
    with session_scope() as s:
        measurements = s.query(Measurement).filter(Measurement.document_id == machine.document.document_id).all()
        assert len(measurements) > 0


def test_prevent_measurement_start_if_no_patient_is_selected(machine_without_patient):
    machine = machine_without_patient
    machine.active_patient = ''
    # start measurement
    machine.main_window.measurement_widget.start_button.clicked.emit()
    app.processEvents()
    errors = caught_exceptions()
    assert len(errors) == 1
    assert 'Invalid patient' in errors[0].message


def test_prevent_measurement_start_if_no_sensor_is_connected(machine):
    # unregister sensors
    producer = machine.producer_process.producer
    for sensor in producer.sensors:
        producer.unregister_sensor(sensor)
    # start measurement
    machine.main_window.measurement_widget.start_button.clicked.emit()
    app.processEvents()
    errors = caught_exceptions()
    assert len(errors) == 1
    assert 'No sensors connected' in errors[0].message
    # machine rolled back to initial state
    assert not machine.in_state(machine.s2)
    assert machine.in_state(machine.s1)


def test_event_detection_state_flow(machine):
    # assign document
    machine.document = machine.s2.create_document()
    # enter sensor info and document
    machine.sensor.enter_info_to_database()
    with session_scope() as s:
        s.add(machine.document)
    # generate and enter data
    n = 10
    time_s = list(range(n))
    torque_Nm = list(range(n))
    insert_time_series_to_database(time_s, torque_Nm, machine.document)
    # trigger transition from s1 to s3 (EventDetectionState)
    machine.transition_map[machine.s1][machine.s3].emit()
    app.processEvents()
    # select regions
    region_count = 2
    machine.s3.dialog.set_add_count(region_count)
    machine.s3.dialog.add_button_clicked()
    app.processEvents()
    # trigger transition from s3 to s4
    machine.transition_map[machine.s3][machine.s4].emit()
    app.processEvents()
    # trigger transition back to s3 (i.e., click No on "are you sure?" prompt)
    machine.transition_map[machine.s4][machine.s3].emit()
    app.processEvents()
    # verify that no annotated events were entered
    with session_scope() as s:
        events = s.query(AnnotatedEvent).filter(AnnotatedEvent.document_id == machine.document.document_id).all()
        assert len(events) == 0
    # trigger transition from s3 to s4
    machine.transition_map[machine.s3][machine.s4].emit()
    app.processEvents()
    # trigger transition from s4 to s5 (i.e., click Yes on "are you sure?" prompt)
    machine.transition_map[machine.s4][machine.s5].emit()
    app.processEvents()
    # verify that annotated events were entered
    with session_scope() as s:
        events = s.query(AnnotatedEvent).filter(AnnotatedEvent.document_id == machine.document.document_id).all()
        assert len(events) == region_count
        region_edits = [machine.s3.dialog.get_region_edit(i) for i in range(region_count)]
        # verify region edges
        for region_edit, event in zip(region_edits, events):
            assert region_edit.left_edge() == event.event_begin
            assert region_edit.right_edge() == event.event_end
    # transition from s5 to s6 has been triggered automatically
    # trigger transition from s6 to s7 (i.e., click Ok on NotesWindow)
    machine.s6.signal_ok.emit()
    app.processEvents()
    # trigger transition back to s6 (i.e., click No on "are you sure?" prompt)
    machine.s7.signal_no.emit()
    app.processEvents()
    # enter data in NotesWindow
    notes = 'foo'
    full_turn_count = 1.2
    distraction_plan_followed = True
    machine.s6.dialog.notes = notes
    machine.s6.dialog.full_turn_count = full_turn_count
    machine.s6.dialog.distraction_plan_followed = distraction_plan_followed
    # trigger transition from s6 to s7 (i.e., click Ok on NotesWindow)
    machine.s6.signal_ok.emit()
    app.processEvents()
    # trigger transition from s7 to s1 (i.e., click Yes on "are you sure?" prompt)
    machine.s7.signal_yes.emit()
    app.processEvents()
    # verify that document updates were entered to database
    with session_scope() as s:
        document = s.query(Document).filter(Document.document_id == machine.document.document_id).first()
        assert document.notes == notes
        assert document.distraction_plan_followed == distraction_plan_followed
        assert float(document.full_turn_count) == full_turn_count


def test_are_you_sure_state_opens_dialog_on_entry_and_closes_on_exit():
    event = QEvent(QEvent.None_)
    state = AreYouSureState('foo')
    state.onEntry(event)
    assert state.dialog.isVisible()
    state.onExit(event)
    assert not state.dialog.isVisible()
