import multiprocessing as mp
import time
import random
import datetime
import pandas as pd

from craniodistractor.core.packet import Packet

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
    
        
if __name__ == '__main__':
    e = mp.Event()
    q = mp.Queue()
    p = mp.Process(name='Producer', target=producer, args=(q, e))
    print(run_and_print(p, q, e, 2))