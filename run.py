import sys
import random
import datetime
import logging
import multiprocessing as mp
from daqstore.store import DataStore
from cranio.producer import ProducerProcess, Sensor, ChannelInfo
from cranio.imada import ImadaSensor
from cranio.app import app
from cranio.app.plot import PlotWindow

start_time = datetime.datetime.now()
n_seconds = 3

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
    ''' Runs the cranio prototype '''
    DataStore.queue_cls = mp.Queue
    store = DataStore(buffer_length=10, resampling_frequency=None)
    #store.plotter = w
    producer_process = ProducerProcess('Imada torque producer', store=store)
    # add imada sensor
    #s = plug_imada_sensor(w.producer_process)
    
    # add dummy sensor with a torque channel
    s = plug_dummy_sensor(producer_process)
    
    # set axis labels
    #w.x_label = 'time (s)'
    #w.y_label = str(s.channels[0])
    p = PlotWindow(producer_process)
    p.ok_button.setText('Analyze')
    logging.info('Exec plot window')
    return p.exec_()


if __name__ == '__main__':
    sys.exit(run())