import pytest
import logging
import time
from sqlalchemy.exc import IntegrityError
from cranio.utils import log_level_to_name, utc_datetime
from cranio.database import init_database, Log, session_scope, Session

logger_name = 'cranio'
logger = logging.getLogger(logger_name)


def test_logging_fails_if_no_session_is_initialized():
    # initialize database but session uninitialized
    init_database()
    with pytest.raises(IntegrityError):
        logger.info('This should raise an IntegrityError')


def test_logging_is_directed_to_database_log_table_with_correct_values(database_fixture):
    wait_duration = 0.01  # seconds
    t_start = utc_datetime()
    # short wait to ensure that t_start < log timestamp
    time.sleep(wait_duration)
    msg = 'This should not raise an IntegrityError'
    logger.info(msg)
    # short wait to ensure that t_stop > log timestamp
    time.sleep(wait_duration)
    t_stop = utc_datetime()
    with session_scope() as s:
        logs = s.query(Log).all()
        assert len(logs) == 1
        log = logs[0]
        assert log.message == msg
        assert log.session_id == Session.get_instance().session_id
        assert log.logger == logger_name
        assert log_level_to_name(log.level).lower() == 'info'
        # verify that the log entry is created between t_start and current time
        assert t_start <= log.created_at <= t_stop
