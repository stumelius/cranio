import logging
from cranio.utils import log_level_to_name
from cranio.database import session_scope, Log


def test_database_handler(database_document_fixture):
    logger = logging.getLogger('cranio')
    logger.info('foo')
    with session_scope() as s:
        logs = s.query(Log).all()
        assert len(logs) == 1
        log = logs[0]
        assert log.message == 'foo'
        assert log_level_to_name(log.level) == 'INFO'
        assert log.logger == 'cranio'