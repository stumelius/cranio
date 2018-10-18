import sys
from cranio.app import app
from cranio.utils import attach_excepthook, logger, configure_logging
from cranio.database import init_database, Session
from cranio.state import MyStateMachine
from cranio.constants import SQLITE_FILENAME

# initialize database and session
init_database(f'sqlite:///{SQLITE_FILENAME}')
Session.init()
# attach custom excepthook
attach_excepthook()


def run():
    """
    Run the craniodistractor application.

    :return: 
    """
    machine = MyStateMachine()
    logger.register_machine(machine)
    logger.info('Start state machine')
    machine.start()
    ret = app.exec_()
    logger.info('Stop state machine')
    machine.stop()
    return ret


if __name__ == '__main__':
    configure_logging()
    sys.exit(run())
