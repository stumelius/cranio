import pytest
import logging.config
from cranio.database import init_database, Session, Patient, Document, clear_database
from cranio.utils import get_logging_config
from cranio.core import generate_unique_id


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
    try:
        Document.init(patient_id=Patient.instance_id)
    except ValueError:
        Document.reset_instance()
        Document.init(patient_id=Patient.instance_id)


@pytest.fixture(scope='session', autouse=True)
def logging_fixture():
    logging.config.dictConfig(get_logging_config())