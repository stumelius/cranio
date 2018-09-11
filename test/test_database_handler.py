import logging
from cranio.utils import log_level_to_name, logger
from cranio.database import session_scope, Log


def test_database_handler(database_document_fixture):
    logger.info('foo')
    with session_scope() as s:
        logs = s.query(Log).filter(Log.level == logging.INFO, Log.message == 'foo').all()
        assert len(logs) == 1
        log = logs[0]
        assert log_level_to_name(log.level) == 'INFO'
        assert log.logger == 'cranio'
