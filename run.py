import sys
import logging
import logging.config
import multiprocessing as mp
from daqstore.store import DataStore
from cranio.app import app
from cranio.app.window import MainWindow
from cranio.utils import get_logging_config
from cranio.database import init_database, Session

# logging configuration
d = get_logging_config()
logging.config.dictConfig(d)
# initialize database and session
init_database()
Session.init()


def run():
    """
    Run the craniodistractor application.

    :return: 
    """
    # use multiprocessing queue
    DataStore.queue_cls = mp.Queue
    w = MainWindow()
    logging.info('Opening main window ...')
    w.show()
    ret = app.exec_()
    logging.info('Exiting application ...')
    return ret


if __name__ == '__main__':
    sys.exit(run())
