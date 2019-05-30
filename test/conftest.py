import pytest
import logging.config
from cranio.model import Database, Session, Patient, Document, DistractorType
from cranio.utils import get_logging_config, generate_unique_id, utc_datetime, logger
from cranio.producer import ProducerProcess, Sensor
from cranio.state_machine import StateMachine
from cranio.app import app
from config import Config


@pytest.fixture(scope='function')
def database_fixture():
    database = Database(drivername='sqlite')
    logger.register_database(database)
    database.create_engine()
    try:
        Session.init(database=database)
    except ValueError:
        Session.reset_instance()
        Session.init(database=database)
    yield database
    logger.unregister_database(database)
    database.clear()


@pytest.fixture(scope='function')
def database_patient_fixture(database_fixture):
    patient_id = generate_unique_id()
    try:
        Patient.init(patient_id=patient_id, database=database_fixture)
    except ValueError:
        Patient.reset_instance()
        Patient.init(patient_id=patient_id, database=database_fixture)
    yield database_fixture


@pytest.fixture(scope='function')
def database_document_fixture(database_patient_fixture):
    Sensor.enter_info_to_database(database=database_patient_fixture)
    try:
        Document.init(
            patient_id=Patient.get_instance().patient_id,
            sensor_serial_number=Sensor.sensor_info.sensor_serial_number,
            distractor_type=Config.DEFAULT_DISTRACTOR,
            database=database_patient_fixture
        )
    except ValueError:
        Document.reset_instance()
        Document.init(
            patient_id=Patient.get_instance().patient_id,
            sensor_serial_number=Sensor.sensor_info.sensor_serial_number,
            distractor_type=Config.DEFAULT_DISTRACTOR,
            database=database_patient_fixture
        )
    yield database_patient_fixture


@pytest.fixture(scope='session', autouse=True)
def logging_fixture():
    logging.config.dictConfig(get_logging_config())


@pytest.fixture
def producer_process():
    p = ProducerProcess('test_process', document=Document(document_id=generate_unique_id(), started_at=utc_datetime()))
    yield p
    if p.is_alive():
        p.join()
    assert not p.is_alive()


@pytest.fixture(scope='function')
def machine(producer_process, database_patient_fixture):
    state_machine = StateMachine(database=database_patient_fixture)
    logger.register_machine(state_machine)
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
    state_machine = StateMachine(database=database_fixture)
    logger.register_machine(state_machine)
    state_machine.main_window.producer_process = producer_process
    state_machine.start()
    app.processEvents()
    yield state_machine
    # kill producer
    if state_machine.producer_process.is_alive():
        state_machine.producer_process.join()
    state_machine.stop()
