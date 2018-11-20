import pytest
import logging.config
from cranio.model import Database, Session, Patient, Document, DistractorType
from cranio.utils import get_logging_config, generate_unique_id, utc_datetime, logger
from cranio.producer import ProducerProcess, Sensor


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
        Document.init(patient_id=Patient.get_instance().patient_id,
                      sensor_serial_number=Sensor.sensor_info.sensor_serial_number,
                      distractor_type=DistractorType.KLS, database=database_patient_fixture)
    except ValueError:
        Document.reset_instance()
        Document.init(patient_id=Patient.get_instance().patient_id,
                      sensor_serial_number=Sensor.sensor_info.sensor_serial_number,
                      distractor_type=DistractorType.KLS, database=database_patient_fixture)
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
