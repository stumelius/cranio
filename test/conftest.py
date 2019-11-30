import pytest
import logging
import logging.config
from typing import Tuple
from cranio.model import Database, Session, Patient, Document, SensorInfo
from cranio.utils import get_logging_config, generate_unique_id, utc_datetime, logger
from cranio.producer import ProducerProcess
from cranio.state_machine import StateMachine
from cranio.app import app
from config import Config


@pytest.fixture(scope='function')
def database_fixture():
    database = Database(drivername='sqlite')
    database.create_engine()
    logger.register_database(database)
    database.init()
    yield database
    logger.unregister_database(database)
    database.clear()


@pytest.fixture(scope='session', autouse=True)
def logging_fixture():
    logging.config.dictConfig(get_logging_config())


@pytest.fixture
def producer_process():
    p = ProducerProcess(
        'test_process',
        document=Document(document_id=generate_unique_id(), started_at=utc_datetime()),
    )
    yield p
    if p.is_alive():
        p.join()
    assert not p.is_alive()


@pytest.fixture(scope='function')
def machine(producer_process, database_fixture):
    state_machine = StateMachine(database=database_fixture)
    state_machine.active_session = add_session(database_fixture)
    state_machine.active_patient = add_patient(database_fixture)
    logger.register_machine(state_machine)
    state_machine.main_window.producer_process = producer_process
    # Connect and register dummy sensor
    state_machine.main_window.connect_dummy_sensor()
    state_machine.main_window.register_sensor_with_producer()
    state_machine.start()
    app.processEvents()
    yield state_machine
    # Kill producer
    state_machine.producer_process.join()
    state_machine.stop()


@pytest.fixture
def machine_without_patient(producer_process, database_fixture):
    state_machine = StateMachine(database=database_fixture)
    state_machine.active_session = add_session(database_fixture)
    logger.register_machine(state_machine)
    state_machine.main_window.producer_process = producer_process
    state_machine.start()
    app.processEvents()
    yield state_machine
    # kill producer
    if state_machine.producer_process.is_alive():
        state_machine.producer_process.join()
    state_machine.stop()


@pytest.helpers.register
def transition_machine_to_s1(machine):
    machine.s0.signal_ok.emit()
    assert machine.in_state(machine.s1)


@pytest.helpers.register
def add_session(database: Database) -> Session:
    with database.session_scope() as s:
        session = Session()
        s.add(session)
    return session


@pytest.helpers.register
def add_patient(database: Database) -> Patient:
    with database.session_scope() as s:
        patient = Patient(patient_id=generate_unique_id())
        s.add(patient)
    return patient


@pytest.helpers.register
def add_sensor_info(database: Database) -> SensorInfo:
    with database.session_scope() as s:
        sensor_info = SensorInfo(sensor_serial_number='pytest', turns_in_full_turn=3)
        s.add(sensor_info)
    return sensor_info


@pytest.helpers.register
def add_document_and_foreign_keys(
    database: Database
) -> Tuple[Document, Patient, Session, SensorInfo]:
    session = add_session(database)
    patient = add_patient(database)
    sensor_info = add_sensor_info(database)
    with database.session_scope() as s:
        document = Document(
            session_id=session.session_id,
            patient_id=patient.patient_id,
            sensor_serial_number=sensor_info.sensor_serial_number,
            distractor_type=Config.DEFAULT_DISTRACTOR,
        )
        s.add(document)
    return document, patient, session, sensor_info
