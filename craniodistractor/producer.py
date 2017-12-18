'''
Module description.

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
import datetime
import pandas as pd

from craniodistractor.core.packet import Packet

from contextlib import contextmanager
    
def all_from_queue(q):
    while not q.empty():
        yield q.get()

def datetime_to_seconds(arr, t0):
    # employ conversion to pd.Timestamp for datetime and np.datetime support
    _func = lambda x: (pd.Timestamp(x)-t0).total_seconds()
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
        '''
        Reads values from the sensor channels.
        '''
        if len(self.channels) == 0:
            return None
        values = {}
        for c in self.channels:
            values[str(c)] = None
        return Packet([datetime.datetime.utcnow()], values)

class Producer:
    
    def __init__(self):
        self.sensors = []
        
    def open(self):
        for s in self.sensors:
            s.open()
    
    def close(self):
        for s in self.sensors:
            s.close()
        
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
        '''
        Runs the producer process. Data Packets are put to data_queue.
        '''
        # implement required initializations here!
        self.start_event.wait()
        # open producer
        with open_port(self.producer):
            while self.start_event.is_set():
                data = self.producer.read()
                if len(data) > 0:
                    self.data_queue.put(data)