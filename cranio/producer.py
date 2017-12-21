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
import itertools
import multiprocessing as mp
import pandas as pd

from cranio.core import Packet

from contextlib import contextmanager
import logging
    
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
                    data = self.producer.read()
                    if len(data) > 0:
                        self.data_queue.put(data)
        logging.info('Stopping producer process "{}"'.format(str(self)))
                    
    def get_all(self) -> list:
        '''
        Returns all data from the data queue.
        
        Example:
            data = Packet.concat(process.get_all())
        '''
        return list(itertools.chain(*all_from_queue(self.data_queue)))
                    
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
        self.data_queue.close()
        self.data_queue.join_thread()
        self._process.join(timeout)
        if self.is_alive():
            logging.error('Producer process "{}" is not shutting down gracefully. Resorting to force terminate and join...'.format(str(self)))
            self._process.terminate()
            self._process.join(timeout)
        logging.info('Producer process "{}" joined successfully'.format(str(self)))
        return self._process.exitcode