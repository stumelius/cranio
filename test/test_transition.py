import pytest
from config import Config
from cranio.producer import Sensor
from cranio.app import app


def test_start_measurement_transition_prevents_start_if_no_patient_is_selected(
    machine_without_patient,
):
    machine = machine_without_patient
    machine.active_patient = ''
    # start measurement
    machine.main_window.measurement_widget.start_button.clicked.emit()
    app.processEvents()
    errors = pytest.helpers.caught_exceptions(machine.database)
    assert len(errors) == 1
    assert 'Invalid patient' in errors[0].message


def test_start_measurement_transition_prevents_start_if_no_sensor_is_connected(machine):
    # Unregister connected dummy sensor
    machine.main_window.unregister_sensor()
    # Start measurement
    machine.main_window.measurement_widget.start_button.clicked.emit()
    app.processEvents()
    errors = pytest.helpers.caught_exceptions(machine.database)
    assert len(errors) == 1
    assert (
        errors[0].message
        == 'No available devices detected (ENABLE_DUMMY_SENSOR = False)'
    )
    # Machine rolled back to initial state
    assert not machine.in_state(machine.s2)
    assert machine.in_state(machine.s1)


def test_start_measurement_transition_tries_to_automatically_connect_imada_sensor_but_fails_because_configuration_disables_dummy_sensor(
    machine,
):
    # Disconnect sensor
    machine.main_window.unregister_sensor()
    machine.s1.signal_start.emit()
    assert machine.in_state(machine.s1)
    assert machine.main_window.sensor is None


def test_start_measurement_transition_automatically_connects_dummy_sensor_if_imada_not_available_and_configuration_enables_dummy_sensor(
    machine,
):
    Config.ENABLE_DUMMY_SENSOR = True
    try:
        # Disconnect sensor
        machine.main_window.unregister_sensor()
        machine.s1.signal_start.emit()
        assert machine.in_state(machine.s2)
        assert isinstance(machine.main_window.sensor, Sensor)
        machine.s1.signal_stop.emit()
        assert machine.in_state(machine.s3)
    finally:
        Config.ENABLE_DUMMY_SENSOR = False
