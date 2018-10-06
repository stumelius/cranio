import pytest
import time
import logging
from PyQt5.QtCore import QEvent, Qt
from cranio.app import app
from cranio.state import MyStateMachine, AreYouSureState
from cranio.database import Patient, Document, Measurement, session_scope, insert_time_series_to_database, \
    AnnotatedEvent, Log, SensorInfo, EventType, Session
from cranio.utils import attach_excepthook

wait_sec = 0.5
attach_excepthook()


@pytest.fixture(scope='function')
def machine(producer_process, database_patient_fixture):
    state_machine = MyStateMachine()
    state_machine.main_window.producer_process = producer_process
    # Connect and register dummy sensor
    state_machine.main_window.connect_dummy_sensor()
    state_machine.main_window.register_sensor_with_producer()
    # Set active patient
    state_machine.active_patient = Patient.get_instance().patient_id
    state_machine.start()
    app.processEvents()
    yield state_machine
    # Kill producer
    state_machine.producer_process.join()
    state_machine.stop()


@pytest.fixture
def machine_without_patient(producer_process, database_fixture):
    state_machine = MyStateMachine()
    state_machine.main_window.producer_process = producer_process
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
    # Start measurement
    machine.main_window.measurement_widget.start_button.clicked.emit()
    app.processEvents()
    assert machine.document is not None
    with session_scope() as s:
        document = s.query(Document).first()
        assert document.document_id == machine.document.document_id
        # Verify patient, distractor and operator
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
    # Unregister connected dummy sensor
    machine.main_window.unregister_sensor()
    # Start measurement
    machine.main_window.measurement_widget.start_button.clicked.emit()
    app.processEvents()
    errors = caught_exceptions()
    assert len(errors) == 1
    assert 'No sensors connected' in errors[0].message
    # Machine rolled back to initial state
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
    region_count = machine.s3.region_count()
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
    machine.s6.dialog.notes = notes
    machine.s6.dialog.full_turn_count = full_turn_count
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
        assert float(document.full_turn_count) == full_turn_count


def test_are_you_sure_state_opens_dialog_on_entry_and_closes_on_exit():
    event = QEvent(QEvent.None_)
    state = AreYouSureState('foo')
    state.onEntry(event)
    assert state.dialog.isVisible()
    state.onExit(event)
    assert not state.dialog.isVisible()


def test_note_state_number_of_full_turns_equals_number_of_annotated_events_times_per_turns_in_full_turn(database_document_fixture):
    state_machine = MyStateMachine()
    state_machine.document = Document.get_instance()
    state = state_machine.s6
    event_count = 3
    with session_scope() as s:
        # insert annotated events
        for i in range(event_count):
            s.add(AnnotatedEvent(document_id=state.document.document_id, event_begin=0, event_end=1,
                                 event_num=i+1, annotation_done=True, recorded=True,
                                 event_type=EventType.distraction_event_type().event_type))
    sensor_info = state.document.get_related_sensor_info()
    # trigger entry with dummy event
    event = QEvent(QEvent.None_)
    state.onEntry(event)
    assert state.full_turn_count == event_count / float(sensor_info.turns_in_full_turn)
    assert state.dialog.full_turn_count == event_count / float(sensor_info.turns_in_full_turn)


def test_event_detection_state_default_region_count_equals_turns_in_full_turn(database_document_fixture):
    state_machine = MyStateMachine()
    state_machine.document = Document.get_instance()
    state = state_machine.s3
    sensor_info = state.document.get_related_sensor_info()
    # generate and enter data
    n = 10
    insert_time_series_to_database(list(range(n)), list(range(n)), state.document)
    # trigger entry with dummy event
    event = QEvent(QEvent.None_)
    state.onEntry(event)
    app.processEvents()
    assert state.region_count() == int(sensor_info.turns_in_full_turn)


def test_state_machine_transitions_to_and_from_change_session_state(machine):
    # Add extra session to switch to
    with session_scope() as s:
        s.add(Session())
    assert machine.s1.signal_change_session is not None
    # Trigger transition from s1 to s9 (ChangeSessionState)
    machine.s1.signal_change_session.emit()
    assert machine.in_state(machine.s9)
    # Select session that is not the instance
    assert len(machine.s9.session_widget.sessions) == machine.s9.session_widget.session_count() == 2
    other_sessions = [s for s in machine.s9.session_widget.sessions
                      if s.session_id != Session.get_instance().session_id]
    assert len(other_sessions) == 1
    active_session_id = other_sessions[0].session_id
    machine.s9.session_widget.select_session(active_session_id)
    # Click Select (Trigger transition from s9 to s10)
    machine.s9.signal_select.emit()
    assert machine.in_state(machine.s10)
    # Click No on "Are you sure?" prompt (Trigger transition from s10 back to s9)
    machine.s10.signal_no.emit()
    assert machine.in_state(machine.s9)
    # Click Cancel to go back to s1
    machine.s9.signal_cancel.emit()
    assert machine.in_state(machine.s1)
    # Trigger transition back to s9 (ChangeSessionState)
    machine.s1.signal_change_session.emit()
    assert machine.in_state(machine.s9)
    # Click Select to go to s10
    machine.s9.signal_select.emit()
    # Click Yes on "Are you sure?" prompt (Trigger transition from s10 to s1)
    machine.s10.signal_yes.emit()
    assert machine.in_state(machine.s1)
    # Verify that session has changed
    assert Session.get_instance().session_id == active_session_id


def test_state_machine_change_session_widget_clicking_x_in_top_right_equals_to_cancel_button(machine):
    # Trigger transition from s1 to s9 (ChangeSessionState)
    machine.s1.signal_change_session.emit()
    assert machine.in_state(machine.s9)
    machine.s9.session_dialog.close()
    assert machine.in_state(machine.s1)


def test_press_enter_in_initial_state_is_start_and_enter_in_measurement_state_is_stop(qtbot, machine):
    # Run two loops to verify same behavior when coming back to initial state from measurement state
    for _ in range(2):
        with qtbot.waitSignal(machine.main_window.signal_start):
            qtbot.keyPress(machine.main_window.measurement_widget.start_button, Qt.Key_Enter)
        with qtbot.waitSignal(machine.main_window.signal_stop):
            qtbot.keyPress(machine.main_window.measurement_widget.stop_button, Qt.Key_Enter)


def test_click_close_in_main_window_prompts_verification_from_user(machine):
    # Trigger close and verify that state changed to s11
    machine.main_window.signal_close.emit()
    assert machine.in_state(machine.s11)
    # Trigger No and verify that state is back to s1
    machine.s11.signal_no.emit()
    assert machine.in_state(machine.s1)
    # Trigger close again, trigger Yes and verify that machine has stopped
    machine.main_window.signal_close.emit()
    machine.s11.signal_yes.emit()
    assert not machine.isRunning()