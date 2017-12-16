'''
Test module description

Copyright (C) 2017  Simo Tumelius

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''

import multiprocessing as mp
import time
import datetime
import pandas as pd

from craniodistractor.core.packet import Packet

from contextlib import contextmanager
    
def all_from_queue(q):
    while not q.empty():
        yield q.get()

def datetime_to_seconds(arr, t0):
    _func = lambda x: (x-t0).total_seconds()
    try:
        return list(map(_func, arr))
    except TypeError:
        return _func(arr)

@contextmanager
def open_port(p):
    yield p.open()
    p.close()
    
class ChannelInfo:
    
    strfmt = '{self.name} ({self.unit})' # default string representation
    
    def __init__(self, name, unit):
        self.name = name
        self.unit = unit
        
    def __str__(self):
        return self.strfmt.format(self=self)

class Sensor:
    
    def __init__(self):
        self.channels = []
    
    def open(self):
        pass
    
    def close(self):
        pass
    
    def self_test(self):
        with open_port(self):
            pass
        return True
    
    def add_channel(self, channel_info):
        self.channels.append(channel_info)
        
    def remove_channel(self, channel_info):
        self.channels.remove(channel_info)
    
    def read(self):
        if len(self.channels) == 0:
            return None
        values = {}
        for c in self.channels:
            values[str(c)] = None
        return Packet([datetime.datetime.utcnow()], values)

class Producer:
    
    def __init__(self):
        self.sensors = []
        
    def add_sensor(self, sensor):
        assert sensor.self_test(), 'Sensor did not pass self test'
        self.sensors.append(sensor)
        
    def remove_sensor(self, sensor):
        self.sensors.remove(sensor)
        
    def read(self):
        return [s.read() for s in self.sensors]

class ProducerProcess:
    
    producer_class = Producer
    
    def __init__(self, name):
        self.data_queue = mp.Queue()
        self.start_event = mp.Event()
        self.producer = self.producer_class()
        self._process = mp.Process(name=name, target=self.run)
        
    def __getattr__(self, attr):
        ''' Object composition from self._process (multiprocessing.Process) '''
        if attr in {'__getstate__', '__setstate__'}:
            return object.__getattr__(self, attr)
        if attr in ('start', 'join', 'is_alive'):
            return getattr(self._process, attr)
        raise AttributeError
        
    def run(self):
        # implement required initializations here!
        self.start_event.wait()
        while self.start_event.is_set():
            data = self.producer.read()
            if len(data) > 0:
                self.data_queue.put(pd.concat(map(lambda x: x.as_dataframe(), data)))
        
def test_channel_info():
    c = ChannelInfo('torque', 'Nm')
    assert str(c) == 'torque (Nm)'
            
def test_sensor():
    s = Sensor()
    assert s.self_test()
    assert s.read() == None
    ch = ChannelInfo('torque', 'Nm')
    s.add_channel(ch)
    packet = s.read()
    df = packet.as_dataframe()
    assert not df.empty
    assert list(df.columns) == [str(ch)]
            
def test_producer_add_and_remove_sensors():
    n = 3
    p = Producer()
    sensors = [Sensor() for _ in range(n)]
    for s in sensors:
        p.add_sensor(s)
    assert len(p.sensors) == n
    for s in sensors:
        p.remove_sensor(s)
    assert len(p.sensors) == 0
                
def test_producer_process_start_and_join():
    p = ProducerProcess('test_process')
    p.start()
    assert p.is_alive()
    p.start_event.set()
    time.sleep(0.5)
    p.start_event.clear()
    p.join(0.5)
    assert not p.is_alive()
    
def test_producer_process_with_sensors():
    p = ProducerProcess('test_process')
    s = Sensor()
    channels = [ChannelInfo('torque', 'Nm'), ChannelInfo('load', 'N'), ChannelInfo('extension', 'mm')]
    for c in channels:
        s.add_channel(c)
    p.producer.add_sensor(s)
    p.start()
    assert p.is_alive()
    p.start_event.set()
    time.sleep(0.5)
    p.start_event.clear()
    # NOTE: data_queue must be emptied before joining the thread
    data = pd.concat(all_from_queue(p.data_queue))
    for c in channels:
        assert str(c) in data
    p.join(0.5)
    assert not p.is_alive()