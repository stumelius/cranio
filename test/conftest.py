import pytest
import logging.config
from cranio.model import init_database, Session, Patient, Document, DistractorType
from cranio.utils import get_logging_config, generate_unique_id, utc_datetime
from cranio.producer import ProducerProcess, Sensor


@pytest.fixture(scope='function')
def database_fixture():
    # setup
    init_database()
    try:
        Session.init()
    except ValueError:
        Session.reset_instance()
        Session.init()
    yield


@pytest.fixture(scope='function')
def database_patient_fixture(database_fixture):
    patient_id = generate_unique_id()
    try:
        Patient.init(patient_id=patient_id)
    except ValueError:
        Patient.reset_instance()
        Patient.init(patient_id=patient_id)


@pytest.fixture(scope='function')
def database_document_fixture(database_patient_fixture):
    Sensor.enter_info_to_database()
    try:
        Document.init(patient_id=Patient.get_instance().patient_id,
                      sensor_serial_number=Sensor.sensor_info.sensor_serial_number,
                      distractor_type=DistractorType.KLS)
    except ValueError:
        Document.reset_instance()
        Document.init(patient_id=Patient.get_instance().patient_id,
                      sensor_serial_number=Sensor.sensor_info.sensor_serial_number,
                      distractor_type=DistractorType.KLS)


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
