import sys
import pandas as pd
import random
import datetime

from pyqtgraph.Qt import QtCore
from pyqtgraph import PlotWidget
from craniodistractor.app.plot import PlotWindow, RegionWidget, update_plot, time_filter

p = PlotWindow()
plot_widget = p.add_plot(PlotWidget())
curve = plot_widget.plot()

n_seconds = 3
t0 = datetime.datetime.now()

def update():
    global plot_widget
    time_filter(n_seconds, update_plot(plot_widget, x=[(datetime.datetime.now()-t0).total_seconds()], y=[random.gauss(0,1)]))
    
timer = QtCore.QTimer()
timer.timeout.connect(update)
timer.start(0)

if __name__ == '__main__':
    sys.exit(p.exec_())
