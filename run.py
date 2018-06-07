import sys
import random
import datetime
import logging
import logging.config
import multiprocessing as mp
from daqstore.store import DataStore
from cranio.producer import ProducerProcess, Sensor, ChannelInfo
from cranio.imada import ImadaSensor
from cranio.app.plot import PlotWindow
from cranio.app.dialogs import SessionMetaDialog
from cranio.utils import get_logging_config
from cranio.database import init_database

start_time = datetime.datetime.now()
n_seconds = 3

# logging configuration
d = get_logging_config()
logging.config.dictConfig(d)
# initialize database
init_database()

def update(plot_widget):
    time_filter(n_seconds, update_plot(plot_widget, x=[(datetime.datetime.now()-start_time).total_seconds()], y=[random.gauss(0,1)]))

def random_value_generator():
    return random.gauss(0, 1)

def plug_imada_sensor(producer_process):
    s = ImadaSensor()
    producer_process.producer.add_sensor(s)
    return s

def plug_dummy_sensor(producer_process):
    s = Sensor()
    s._default_value_generator = random_value_generator
    ch = ChannelInfo('torque', 'Nm')
    s.add_channel(ch)
    producer_process.producer.add_sensor(s)
    return s
    
def run():
    ''' Runs the craniodistractor application '''
    DataStore.queue_cls = mp.Queue
    store = DataStore(buffer_length=10, resampling_frequency=None)
    producer_process = ProducerProcess('Imada torque producer', store=store)
    # add imada sensor
    #s = plug_imada_sensor(w.producer_process)
    # add dummy sensor with a torque channel
    s = plug_dummy_sensor(producer_process)
    p = PlotWindow(producer_process)
    p.ok_button.setText('Analyze')
    # session meta prompt before plot window
    logging.info('Open session meta prompt')
    d = SessionMetaDialog()
    if d.exec_():
        logging.info(str(d.session_meta))
        logging.info('Open plot window')
        return p.exec_()
    logging.info('Exiting application ...')
    return 0


if __name__ == '__main__':
    sys.exit(run())