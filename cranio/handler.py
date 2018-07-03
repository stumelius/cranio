import logging
import traceback
from datetime import datetime
from cranio import DEFAULT_DATEFMT
from cranio.database import Log, session_scope, Document


class DatabaseHandler(logging.Handler):
    # A very basic logger that commits a log entry in a database
    def emit(self, record):
        trace = None
        exc = record.__dict__['exc_info']
        if exc:
            trace = traceback.format_exc(exc)
        dt = datetime.strptime(record.__dict__['asctime'], DEFAULT_DATEFMT)
        log = Log(logger=record.__dict__['name'], level=record.__dict__['levelno'],
                  created_at=dt, trace=trace, message=record.__dict__['msg'], document_id=Document.instance_id)
        with session_scope() as s:
            s.add(log)