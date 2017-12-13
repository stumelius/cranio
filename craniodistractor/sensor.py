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
from collections import namedtuple
from contextlib import contextmanager

from craniodistractor.core.packet import Packet

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
        raise ValueError('Invalid telegram: {}'.format(str_))
    unit, mode, condition = str_[-3:]
    return (value, unit, mode, condition)

RS232Configuration = namedtuple('RS232Configuration', ['baudrate', 'bytesize', 'parity', 'stopbits', 'timeout'])

@contextmanager
def open_port(p):
    yield p.open()
    p.close()

class Sensor:
    rs232_config = RS232Configuration(19200, serial.EIGHTBITS, serial.PARITY_NONE, serial.STOPBITS_ONE, 1/50)
    serial_num = 'FTSLQ6QIA'
    
    def __init__(self):
        self.serial = serial.Serial(port=None, **self.rs232_config._asdict())
        self.serial.port = get_com_port(self.serial_num)
        
        self.data = []
        self.active = False
        
    def __getattr__(self, attr):
        ''' Object composition from self.serial '''
        if attr in {'__getstate__', '__setstate__'}:
            return object.__getattr__(self, attr)
        return getattr(self.serial, attr)
    
    def poll(self):
        # ask for display value
        p.write(('D' + EOL).encode('utf-8'))
        # read display value
        str_ = p.readline().decode('utf-8')
        return str_
    
    def start(self):
        self.active = True
        with open_port(self):
            while self.active:
                # decode telegram
                value, unit, mode, condition = decode_telegram(self.poll())
                self.data.append((datetime.datetime.utcnow(), value))
                
    def stop(self):
        self.active = False
    
        
if __name__ == '__main__':
    t_start = datetime.datetime.utcnow()
    p = Sensor()
    p.open()
    values = []
    for i in range(50):
        p.write(('D' + EOL).encode('utf-8'))
        str_ = p.readline().decode('utf-8')
        value, unit, mode, condition = decode_telegram(str_)
        #t = (datetime.datetime.utcnow()-t_start).total_seconds()
        values.append((datetime.datetime.utcnow(), value))
    i, d = zip(*values)
    packet = Packet(i, {'torque (Ncm)': d})
    packet.index = list(map(lambda x: (x - t_start).total_seconds(), packet.index))
    print(packet.as_dataframe())
    print(len(packet.index) / (max(packet.index)-min(packet.index)), 'Hz')
    t_end = datetime.datetime.utcnow()
    
    p.close()
