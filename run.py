import sys
import datetime
import logging
import logging.config
import multiprocessing as mp
from daqstore.store import DataStore
from cranio.app import app
from cranio.app.dialogs import  MainWindow
from cranio.utils import get_logging_config
from cranio.database import init_database

start_time = datetime.datetime.now()
n_seconds = 3

# logging configuration
d = get_logging_config()
logging.config.dictConfig(d)


def run():
    ''' Runs the craniodistractor application '''
    # initialize database
    init_database()
    DataStore.queue_cls = mp.Queue
    w = MainWindow()
    logging.info('Opening main window ...')
    w.show()
    sys.exit(app.exec_())
    logging.info('Exiting application ...')
    return 0


if __name__ == '__main__':
    sys.exit(run())