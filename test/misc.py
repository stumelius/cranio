import multiprocessing as mp
import time
import random
import datetime
import pandas as pd

from pyqtgraph import PlotWidget
from craniodistractor.core.packet import Packet
from craniodistractor.app.plot import PlotWindow, update_plot, time_filter
from craniodistractor.app import app

def producer(q, e):
    while not e.is_set():
        x = [datetime.datetime.now()]
        y = [random.gauss(0, 1) for _ in range(len(x))]
        q.put(Packet(x, {'value': y}))
        time.sleep(0.02)
        
def _read(q):
    return q.get()
    
def _read_all(q):
    while not q.empty():
        yield _read(q)
        
def run_batch(p, q, e, secs):
    p.start()
    time.sleep(secs)
    e.set()
    packets = list(_read_all(q))
    data = pd.concat(map(lambda x: x.as_dataframe(), packets))
    p.join()
    return data

def run_and_print(p, q, e, secs):
    data = pd.DataFrame()
    p.start()
    t0 = time.time()
    while time.time() - t0 < secs:
        packet = _read(q)
        data = pd.concat([data, packet.as_dataframe()])
    e.set()
    p.join()
    return data

def datetime_to_seconds(arr, t0):
    _func = lambda x: (x-t0).total_seconds()
    try:
        return list(map(_func, arr))
    except TypeError:
        return _func(arr)
    
def run_and_plot(p, q, e, secs, plot_widget):
    p.start()
    t0 = datetime.datetime.now()
    while datetime_to_seconds(datetime.datetime.now(), t0) < secs:
        packet = _read(q)
        time_filter(3, update_plot(plot_widget, x=datetime_to_seconds(packet.index, t0), y=packet.data['value']))
        app.processEvents()
    e.set()
    p.join()
        
if __name__ == '__main__':
    e = mp.Event()
    q = mp.Queue()
    p = mp.Process(name='Producer', target=producer, args=(q, e))
    w = PlotWindow()
    plot_widget = w.add_plot(PlotWidget())
    w.show()
    run_and_plot(p, q, e, 10, plot_widget)