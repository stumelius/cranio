import sys
import random
import datetime

from cranio.producer import ProducerProcess
from cranio.imada import ImadaSensor
from cranio.app.plot import PlotWindow, update_plot, time_filter, PlotWidget

start_time = datetime.datetime.now()
n_seconds = 3

def update(plot_widget):
    time_filter(n_seconds, update_plot(plot_widget, x=[(datetime.datetime.now()-start_time).total_seconds()], y=[random.gauss(0,1)]))

def run():
    ''' Runs the cranio prototype '''
    p = PlotWindow()
    p.ok_button.setText('Analyze')
    w = PlotWidget()
    p.add_plot(w)
    w.producer_process = ProducerProcess('Imada torque producer')
    s = ImadaSensor()
    w.producer_process.producer.add_sensor(s)
    return p.exec_()


if __name__ == '__main__':
    sys.exit(run())