import sys
import random
import datetime

from functools import partial
from pyqtgraph.Qt import QtCore
from craniodistractor.app.plot import PlotWindow, update_plot, time_filter, PlotWidget

start_time = datetime.datetime.now()
n_seconds = 3

def update(plot_widget):
    time_filter(n_seconds, update_plot(plot_widget, x=[(datetime.datetime.now()-start_time).total_seconds()], y=[random.gauss(0,1)]))

def run():
    ''' Runs the craniodistractor prototype '''
    p = PlotWindow()
    p.add_plot(PlotWidget())
    return p.exec_()


if __name__ == '__main__':
    sys.exit(run())