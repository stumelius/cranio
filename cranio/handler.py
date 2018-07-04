import logging
import traceback
from datetime import datetime, timedelta
from cranio import DEFAULT_DATEFMT
from cranio.database import Log, session_scope, Session


class DatabaseHandler(logging.Handler):
    # A very basic logger that commits a log entry in a database
    def emit(self, record):
        trace = None
        exc = record.__dict__['exc_info']
        if exc:
            trace = traceback.format_exc(exc)
        dt = datetime.strptime(record.__dict__['asctime'], DEFAULT_DATEFMT) + \
             timedelta(milliseconds=record.__dict__['msecs'])
        log = Log(logger=record.__dict__['name'], level=record.__dict__['levelno'],
                  created_at=dt, trace=trace, message=record.__dict__['msg'], session_id=Session.get_instance())
        with session_scope() as s:
            s.add(log)