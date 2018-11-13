import sys
from cranio.app import app
from cranio.utils import attach_excepthook, logger, configure_logging
from cranio.model import Session, DefaultDatabase
from cranio.state_machine import StateMachine
database = DefaultDatabase.SQLITE
database.create_engine()
Session.init(database=database)
# Attach custom excepthook
attach_excepthook()


def run():
    """
    Run the craniodistractor application.

    :return: 
    """
    machine = StateMachine(database)
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
