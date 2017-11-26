'''
MODULE DESCRIPTION

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
# IMADA HTG2-4 digital force gauge
# SN: FTSLQ6QIA
import serial.tools.list_ports

from contextlib import contextmanager

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
    
def is_port_connected(port):
    ''' Checks if a serial device is connected to a specific port '''
    return any([p for p in serial.tools.list_ports.comports() if p.device == port.device])

class Channel:
    '''
    A single input channel. Devices may consist of one or multiple channels.
    
    Responsible for storing channel related information, such as name and unit.
    '''
    
    def __init__(self, name, unit, parent=None):
        '''
        Args:
            - name: a user-defined name for the channel
            - unit: output unit after conversion (e.g., 'V')
            - parent: parent device
        '''
        self.name = name
        self.unit = unit
        self.parent = parent
        
    def __str__(self):
        return '{self.name} ({self.unit})'.format(self=self)
    
    def __repr__(self):
        return str(self)
    
@contextmanager
def open_port(port):
    port.open()
    yield port
    port.close()
    
if __name__ == '__main__':
    serial_object = serial.Serial(port=None, baudrate=19200, bytesize=serial.EIGHTBITS, 
                                  parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, 
                                  timeout=0.2)
    serial_object.port = get_com_port('FTSLQ6QIA')
    with open_port(serial_object) as p:
        p.write('{}\r\n'.format('I').encode('utf-8'))
        print(p.readline().decode('utf-8'))
    