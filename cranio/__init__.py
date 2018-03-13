import sys
import logging
import os
# version info
__version__ = '0.1.0'
# force PyQt5 instead of PyQt4
os.environ['PYQTGRAPH_QT_LIB'] = 'PyQt5'

# Global logging configuration
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Logging to sys.stdout
h1 = logging.StreamHandler(stream=sys.stdout)   # writes logs to sys.stdout
formatter = logging.Formatter('%(asctime)s.%(msecs)03d;%(threadName)s;%(levelname)s;%(message)s', '%Y-%m-%d %H:%M:%S')
h1.setFormatter(formatter)
logger.addHandler(h1)