"""
Logging handlers.
"""
import logging
import traceback
from datetime import datetime, timedelta
from cranio.constants import DEFAULT_DATEFMT
from cranio.model import Log, Session
from sqlalchemy import inspect
from sqlalchemy.exc import IntegrityError


class DatabaseHandler(logging.Handler):
    """ Logger for committing log entries in a database. """

    def emit(self, record: dict) -> None:
        """
        Overloaded method for handling log records.

        :param record: Log record dictionary
        :return: None
        """
        try:
            session_id = Session.get_instance().session_id
        except AttributeError:
            # no instance set
            session_id = None
        trace = None
        exc_info = record.__dict__['exc_info']
        if exc_info:
            # format_tb returns a list
            trace = ''.join(traceback.format_tb(exc_info[2]))
        dt = datetime.strptime(record.__dict__['asctime'], DEFAULT_DATEFMT) + timedelta(
            milliseconds=record.__dict__['msecs']
        )
        log = Log(
            logger=record.__dict__['name'],
            level=record.__dict__['levelno'],
            created_at=dt,
            trace=trace,
            message=record.__dict__['msg'],
            session_id=session_id,
        )
        database = record.__dict__['database']
        # Insert if database is defined and initialized
        if database is not None:
            if database.initialized:
                database.insert(log)
