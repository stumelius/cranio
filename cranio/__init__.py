import os
import multiprocessing as mp
from daqstore.store import DataStore
# use multiprocessing queue
DataStore.queue_cls = mp.Queue
# version info
__version__ = '0.1.0'
# force PyQt5 instead of PyQt4
os.environ['PYQTGRAPH_QT_LIB'] = 'PyQt5'
DEFAULT_DATEFMT = '%Y-%m-%d %H:%M:%S'