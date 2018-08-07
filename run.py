import sys
import logging
import logging.config
from cranio.app import app
from cranio.utils import get_logging_config, attach_excepthook
from cranio.database import init_database, Session
from cranio.state import MyStateMachine

# logging configuration
d = get_logging_config()
logging.config.dictConfig(d)
# initialize database and session
init_database('sqlite:///cranio.db')
Session.init()
# attach custom excepthook
attach_excepthook()


def run():
    """
    Run the craniodistractor application.

    :return: 
    """
    machine = MyStateMachine()
    logging.info('Start state machine')
    machine.start()
    ret = app.exec_()
    logging.info('Stop state machine')
    machine.stop()
    return ret


if __name__ == '__main__':
    sys.exit(run())
