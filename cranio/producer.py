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
import datetime
import logging
import time
import multiprocessing as mp
import pandas as pd
import numpy as np

from contextlib import contextmanager
from cranio.core import Packet
from cranio.utils import random_value_generator
from daqstore.store import DataStore
    
def all_from_queue(q):
    ''' Reads all data from a Queue and returns a generator '''
    while not q.empty():
        yield q.get()

def datetime_to_seconds(arr, t0):
    ''' Converts datetime to difference in seconds between a reference datetime '''
    # employ conversion to pd.Timestamp for datetime and np.datetime support
    _func = lambda x: (pd.Timestamp(x)-t0).total_seconds()
    try:
        return list(map(_func, arr))
    except TypeError:
        return _func(arr)

@contextmanager
def open_port(p):
    ''' Context manager for opening and closing a port '''
    yield p.open()
    p.close()
    
class ChannelInfo:
    ''' Channel information object '''
    
    # default string representation
    strfmt = '{self.name} ({self.unit})'
        
    def __init__(self, name: str, unit: str):
        self.name = name
        self.unit = unit
        
    def __str__(self):
        return self.strfmt.format(self=self)
    
def _default_value_generator():
    return np.NaN

class Sensor:
    '''
    Sensor object that can contain multiple channels. 
    Channels are stored as ChannelInfo objects. 
    Open(), close() and read() method must be overloaded.
    '''
    
    def __init__(self):
        self.channels = []
        self._default_value_generator = _default_value_generator
    
    def open(self):
        ''' Dummy sensor port open '''
        pass
    
    def close(self):
        ''' Dummy sensor port close '''
        pass
    
    def self_test(self):
        ''' Sensor self test by opening and closing the port '''
        with open_port(self):
            pass
        return True
    
    def add_channel(self, channel_info: ChannelInfo):
        ''' Adds a channel to the sensor '''
        return self.channels.append(channel_info)
        
    def remove_channel(self, channel_info: ChannelInfo):
        ''' Removes a channel from the sensor '''
        return self.channels.remove(channel_info)
    
    def read(self):
        '''
        Dummy method for reading values from the sensor channels.
        '''
        if len(self.channels) == 0:
            return None
        values = {}
        for c in self.channels:
            values[str(c)] = self._default_value_generator()
        # sleep for 10 ms to slow down the sampling
        # if there is no wait between consecutive read() calls,
        # too much data is generated for a plot widget to handle
        time.sleep(0.01)
        return Packet([datetime.datetime.now()], values)

class Producer:
    ''' Producer object that can contain multiple Sensor objects. '''
        
    def __init__(self):
        self.sensors = []
        self.id = DataStore.register_device()
        
    def open(self):
        ''' Opens all sensors '''
        for s in self.sensors:
            s.open()
    
    def close(self):
        ''' Closes all sensors '''
        for s in self.sensors:
            s.close()
        
    def add_sensor(self, sensor: Sensor):
        ''' Adds a sensor to the producer '''
        assert sensor.self_test(), 'Sensor did not pass self test'
        self.sensors.append(sensor)
        
    def remove_sensor(self, sensor: Sensor):
        ''' Removes a sensor from the producer '''
        self.sensors.remove(sensor)
        
    def read(self):
        ''' Reads values from all sensors and returns the values in a list '''
        return [s.read() for s in self.sensors]

class ProducerProcess:
    ''' Process object for running a Producer in '''
    
    # default producer class
    producer_class = Producer
    
    def __init__(self, name: str, store):
        self.store = store
        self.start_event = mp.Event()
        self.stop_event = mp.Event()
        self.producer = self.producer_class()
        self._process = mp.Process(name=name, target=self.run)
        
    def __getattr__(self, attr):
        ''' Object composition from self._process (multiprocessing.Process) '''
        if attr in {'__getstate__', '__setstate__'}:
            return object.__getattr__(self, attr)
        if attr in ('is_alive', 'name'):
            return getattr(self._process, attr)
        raise AttributeError
    
    def __str__(self):
        return self.name
        
    def run(self):
        '''
        Runs the producer process. Data Packets are put to data_queue.
        
        Args:
            None
            
        Returns:
            None
            
        Raises:
            None
        '''
        # implement required initializations here!
        # open producer
        logging.info('Running producer process "{}"'.format(str(self)))
        with open_port(self.producer):
            while not self.stop_event.is_set():
                if self.start_event.is_set():
                    for packet in self.producer.read():
                        tpl = (self.producer.id,) + packet.as_tuple()
                        self.store.put(tpl)
        logging.info('Stopping producer process "{}"'.format(str(self)))
                    
    def read(self, include_cache: bool=False) -> pd.DataFrame:
        ''' Returns all data from the data store '''
        return self.store.get_data(include_cache=include_cache)
                    
    def start(self):
        '''
        Starts the producer in a separate process. If process is already running, only the producer is started.
        
        Args:
            None
            
        Returns:
            None
            
        Raises:
            None
        '''
        self.stop_event.clear()
        if not self.is_alive():
            self._process.start()
        self.start_event.set()
        
    def resume(self):
        '''
        Resumes the producer process.
        
        Args:
            None
            
        Returns:
            None
            
        Raises:
            None
        '''
        self.start_event.set()
        
    def pause(self):
        '''
        Pauses the producer. To stop the producer process, call .join() after .pause().
        
        Example:
            process.start()
            time.sleep(2)
            process.pause()
            data = process.get_all()
            process.join()
            assert not process.is_alive()
            
        Args:
            None
            
        Returns:
            None
            
        Raises:
            None
        '''
        self.start_event.clear()
        
    def join(self, timeout=1):
        '''
        Joins the process. If the process won't shut down gracefully, it is forcefully terminated.
        
        Args:
            - timeout: join timeout in seconds
            
        Returns:
            Process exit code
            
        Raises:
            None
        '''
        self.stop_event.set()
        # close the queue and join the background thread
        #self.data_queue.close()
        #self.data_queue.join_thread()
        self._process.join(timeout)
        if self.is_alive():
            logging.error('Producer process "{}" is not shutting down gracefully. Resorting to force terminate and join...'.format(str(self)))
            self._process.terminate()
            self._process.join(timeout)
        logging.info('Producer process "{}" joined successfully'.format(str(self)))
        return self._process.exitcode


def plug_dummy_sensor(producer_process):
    s = Sensor()
    s._default_value_generator = random_value_generator
    ch = ChannelInfo('torque', 'Nm')
    s.add_channel(ch)
    producer_process.producer.add_sensor(s)
    logging.debug('Dummy torque sensor plugged')
    return s
