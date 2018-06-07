import pytest
import logging
import logging.config
from cranio.utils import get_logging_config
from cranio.database import init_database, session_scope, Log, LogLevel


logging.config.dictConfig(get_logging_config())


def test_database_handler():
    init_database()
    logger = logging.getLogger('cranio')
    logger.info('foo')
    with session_scope() as s:
        logs = s.query(Log).all()
        assert len(logs) == 1
        log = logs[0]
        assert log.message == 'foo'
        assert log.level == LogLevel.INFO
        assert log.logger == 'cranio'