"""
Interface for Imada HTG2-4 digital torque gauge.
"""
import re
import serial.tools.list_ports
import datetime
from collections import namedtuple
from typing import Tuple
from serial.tools.list_ports_common import ListPortInfo
from cranio.producer import Sensor, ChannelInfo, ProducerProcess
from cranio.database import SensorInfo
from cranio.utils import logger, utc_datetime

IMADA_EOL = '\r'


class TelegramError(Exception):
    """ Telegram error. """
    pass


def find_serial_device(serial_number: str) -> ListPortInfo:
    """
    Find a serial device with a specific serial number.

    :param serial_number: Device serial number
    :return: Serial port info
    :raises ValueError: if no device found
    """
    try:
        return [port for port in serial.tools.list_ports.comports() if port.serial_number == serial_number][0]
    except IndexError:
        raise ValueError('No device found with serial number {}'.format(serial_number))


def get_com_port(serial_number: str) -> str:
    """
    Find a COM port for a serial device with a specific serial number.

    :param serial_number: Device serial number
    :return: COM port name
    :raises ValueError: if no device found
    """
    return find_serial_device(serial_number).device


def decode_telegram(telegram: str) -> Tuple[str, str, str, str]:
    """
    Decode a telegram string and return a tuple (value, unit, mode, condition).

    :param telegram: Telegram string
    :return: Tuple (value, unit, mode, condition)
    :raises TelegramError: if telegram is invalid
    """
    str_ = telegram.replace(IMADA_EOL, '')
    try:
        value = float(re.findall(r'[-+]?\d*\.\d+|\d+', str_)[0])
    except IndexError:
        raise TelegramError('Invalid telegram: ' + str_)
    try:
        unit, mode, condition = str_[-3:]
    except ValueError:
        raise TelegramError('Invalid telegram: ' + str_)
    return value, unit, mode, condition


# RS232 communication protocol configuration
RS232Configuration = namedtuple('RS232Configuration', ['baudrate', 'bytesize', 'parity', 'stopbits', 'timeout'])


class Imada(Sensor):
    """ Imada HTG2-4 digital torque gauge with USB serial (RS-232) interface. """
    rs232_config = RS232Configuration(19200, serial.EIGHTBITS, serial.PARITY_NONE, serial.STOPBITS_ONE, 1/50)
    sensor_info = SensorInfo(sensor_serial_number='FTSLQ6QIA')

    def __init__(self):
        super().__init__()
        self.serial = serial.Serial(port=None, **self.rs232_config._asdict())
        self.serial.port = get_com_port(self.sensor_info.sensor_serial_number)
        self.register_channel(ChannelInfo('torque', 'Nm'))
    
    def open(self):
        """
        Open the serial port.

        :return:
        """
        return self.serial.open()
    
    def close(self):
        """
        Close the serial port.

        :return:
        """
        return self.serial.close()
    
    def readline(self) -> str:
        """
        Read bytes from the serial port until an EOL character and returns a string.

        :return: String
        """
        line = []
        while True:
            c = self.serial.read().decode('utf-8')
            if c == IMADA_EOL:
                break
            line.append(c)
        return ''.join(line)
    
    def poll(self) -> str:
        """
        Poll the display value from the sensor. To decode the display value string, use decode_telegram().

        :return: Display value as a string
        """
        # request display value
        self.serial.write(('D' + IMADA_EOL).encode('utf-8'))
        # return display value
        return self.readline()
    
    def read(self) -> Tuple[datetime.datetime, dict]:
        """
        Read a single value from the sensor.

        :return: Datetime and value dictionary as a tuple
        """
        try:
            telegram = self.poll()
            value, _, _, _ = decode_telegram(telegram)
        except TelegramError as e:
            logger.error('Decode telegram failed! {}'.format(str(e)))
            value = None
        return utc_datetime(), {str(self.channels[0]): value}


def plug_imada(producer_process: ProducerProcess) -> Imada:
    """
    Plug Imada digital torque gauge to a producer process.

    :param producer_process: Producer process
    :return: Imada object
    """
    imada = Imada()
    producer_process.producer.register_sensor(imada)
    return imada
