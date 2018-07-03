import re
import serial.tools.list_ports
import datetime
import logging

from collections import namedtuple
from typing import Tuple
from cranio.producer import Sensor, ChannelInfo
from cranio.core import Packet

class TelegramError(Exception):
    pass

IMADA_EOL = '\r'

def find_serial_device(serial_number: str):
    '''
    Finds a serial device with a specific serial number.
    
    Args:
        - serial_number: device serial number
        
    Returns:
        Serial port
        
    Raises:
        ValueError: No device found
    '''
    try:
        return [port for port in serial.tools.list_ports.comports() if port.serial_number == serial_number][0]
    except IndexError:
        raise ValueError('No device found with serial number {}'.format(serial_number))

def get_com_port(serial_number: str) -> str:
    '''
    Finds a COM port for a serial device with a specific serial number.
    
    Args:
        - serial_number: device serial number
        
    Returns:
        COM port name as a string
        
    Raises:
        ValueError: No device found
    '''
    return find_serial_device(serial_number).device

def decode_telegram(telegram: str) -> Tuple[str, str, str, str]:
    '''
    Decodes a telegram string and returns a tuple (value, unit, mode, condition).
    
    Args:
        - telegram: telegram string
        
    Returns:
        A tuple (value, unit, mode, condition)
        
    Raises:
        TelegramError: Invalid telegram
    '''
    str_ = telegram.replace(IMADA_EOL, '')
    try:
        value = float(re.findall(r'[-+]?\d*\.\d+|\d+', str_)[0])
    except IndexError:
        raise TelegramError('Invalid telegram: ' + str_)
    try:
        unit, mode, condition = str_[-3:]
    except ValueError:
        raise TelegramError('Invalid telegram: ' + str_)
    return (value, unit, mode, condition)

# RS232 communication protocol configuration
RS232Configuration = namedtuple('RS232Configuration', ['baudrate', 'bytesize', 'parity', 'stopbits', 'timeout'])

class ImadaSensor(Sensor):
    rs232_config = RS232Configuration(19200, serial.EIGHTBITS, serial.PARITY_NONE, serial.STOPBITS_ONE, 1/50)
    serial_number = 'FTSLQ6QIA'
    
    def __init__(self):
        super(ImadaSensor, self).__init__()
        self.serial = serial.Serial(port=None, **self.rs232_config._asdict())
        self.serial.port = get_com_port(self.serial_number)
        self.add_channel(ChannelInfo('torque', 'Nm'))
    
    def open(self):
        '''
        Opens the serial port.
        
        Args:
            None
            
        Returns:
            None
        
        Raises:
            None
        '''
        return self.serial.open()
    
    def close(self):
        '''
        Closes the serial port.
        
        Args:
            None
            
        Returns:
            None
        
        Raises:
            None
        '''
        return self.serial.close()
    
    def readline(self) -> str:
        '''
        Reads bytes from the serial port until an EOL character and returns a string.
        
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
            if c == IMADA_EOL:
                break
            line.append(c)
        return ''.join(line)
    
    def poll(self) -> str:
        '''
        Polls the display value from the sensor. To decode the display value string, use decode_telegram().
        
        Args:
            None
            
        Returns:
            Display value as a string, or telegram
            
        Raises:
            None
        '''
        # ask for display value
        self.serial.write(('D' + IMADA_EOL).encode('utf-8'))
        # return display value
        return self.readline()
    
    def read(self) -> Packet:
        '''
        Reads a single display from the sensor and returns a Packet.
        
        Args:
            None
            
        Returns:
            A Packet object
            
        Raises:
            None
        '''
        try:
            telegram = self.poll()
            value, _, _, _ = decode_telegram(telegram)
        except TelegramError as e:
            logging.error('Decode telegram failed! {}'.format(str(e)))
            value = None
        record = Packet([datetime.datetime.now()], {str(self.channels[0]): value})
        return record


def plug_imada_sensor(producer_process):
    s = ImadaSensor()
    producer_process.producer.add_sensor(s)
    return s