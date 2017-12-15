'''
Implements the USB torque sensor (IMADA HTG2-4) interface.

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
import serial.tools.list_ports
import re
import numpy as np
import pandas as pd
import datetime
import time
import logging
import multiprocessing as mp
from collections import namedtuple
from contextlib import contextmanager

from craniodistractor.core.packet import Packet

class TelegramError(Exception):
    pass

def find_serial_device(serial_number):
    ''' Finds a serial device with a specific serial number '''
    try:
        return [port for port in serial.tools.list_ports.comports() if port.serial_number == serial_number][0]
    except IndexError:
        raise ValueError('No device found with serial number {}'.format(serial_number))

def get_com_port(serial_number):
    ''' Finds a COM port for a serial device with a specific serial number '''
    try:
        return find_serial_device(serial_number).device
    except IndexError:
        raise ValueError('No device found with serial number {}'.format(serial_number))

EOL = '\r'

def decode_telegram(str_):
    ''' Decodes a telegram string and returns a tuple (value, unit, mode, condition) '''
    str_ = str_.replace(EOL, '')
    try:
        value = float(re.findall(r'[-+]?\d*\.\d+|\d+', str_)[0])
    except IndexError:
        raise TelegramError(str_)
    try:
        unit, mode, condition = str_[-3:]
    except ValueError:
        raise TelegramError(str_)
    return (value, unit, mode, condition)

RS232Configuration = namedtuple('RS232Configuration', ['baudrate', 'bytesize', 'parity', 'stopbits', 'timeout'])

@contextmanager
def open_port(p):
    yield p.open()
    p.close()
    
def _read(q):
    return q.get()
    
def _read_all(q):
    while not q.empty():
        yield _read(q)
        
def datetime_to_seconds(arr, t0):
    _func = lambda x: (x-t0).total_seconds()
    try:
        return list(map(_func, arr))
    except TypeError:
        return _func(arr)

def producer(queue, start_event):
    p = Sensor(queue, start_event)
    start_event.wait()
    p.start()

class Sensor:
    rs232_config = RS232Configuration(19200, serial.EIGHTBITS, serial.PARITY_NONE, serial.STOPBITS_ONE, 1/50)
    serial_num = 'FTSLQ6QIA'
    
    def __init__(self, queue, start_event):
        self.serial = serial.Serial(port=None, **self.rs232_config._asdict())
        self.serial.port = get_com_port(self.serial_num)
        self.start_event = start_event
        self.queue = queue
        
    def __getattr__(self, attr):
        ''' Object composition from self.serial '''
        if attr in {'__getstate__', '__setstate__'}:
            return object.__getattr__(self, attr)
        return getattr(self.serial, attr)
    
    def readline(self):
        '''
        Reads bytes from the serial port until an EOL character.
        
        Args:
            None
        
        Returns:
            A string
            
        Raises:
            None
        '''
        line = []
        while True:
            c = self.read().decode('utf-8')
            if c == EOL:
                break
            line.append(c)
        return ''.join(line)
    
    def poll(self):
        # ask for display value
        self.write(('D' + EOL).encode('utf-8'))
        # return display value
        return self.readline()
    
    def start(self):
        with open_port(self):
            while self.start_event.is_set():
                # decode telegram
                try:
                    telegram = self.poll()
                    value, unit, mode, condition = decode_telegram(telegram)
                    #if value > 10:
                        #print(telegram)
                        #print(telegram.encode())
                    record = Packet([datetime.datetime.utcnow()], {'torque (Nm)': value})
                    self.queue.put(record)
                except TelegramError as e:
                    logging.error('Decode telegram failed! {}'.format(str(e)))
                
    def stop(self):
        pass