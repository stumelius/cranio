import re
import serial.tools.list_ports
import pandas as pd
import datetime
import time
import logging
from collections import namedtuple

from craniodistractor.producer import ProducerProcess, Sensor, ChannelInfo, all_from_queue
from craniodistractor.core.packet import Packet

class TelegramError(Exception):
    pass

EOL = '\r'

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

class ImadaSensor(Sensor):
    rs232_config = RS232Configuration(19200, serial.EIGHTBITS, serial.PARITY_NONE, serial.STOPBITS_ONE, 1/50)
    serial_num = 'FTSLQ6QIA'
    
    def __init__(self, *args, **kwargs):
        super(ImadaSensor, self).__init__()
        self.serial = serial.Serial(port=None, **self.rs232_config._asdict())
        self.serial.port = get_com_port(self.serial_num)
        self.add_channel(ChannelInfo('torque', 'Nm'))
    
    def open(self):
        return self.serial.open()
    
    def close(self):
        return self.serial.close()
    
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
            c = self.serial.read().decode('utf-8')
            if c == EOL:
                break
            line.append(c)
        return ''.join(line)
    
    def poll(self):
        # ask for display value
        self.serial.write(('D' + EOL).encode('utf-8'))
        # return display value
        return self.readline()
    
    def read(self):
        try:
            telegram = self.poll()
            value, unit, mode, condition = decode_telegram(telegram)
        except TelegramError as e:
            logging.error('Decode telegram failed! {}'.format(str(e)))
            value = None
        record = Packet([datetime.datetime.utcnow()], {str(self.channels[0]): value})
        return record