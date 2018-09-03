"""
.. todo:: Module description
"""
import datetime
import time
import multiprocessing as mp
import pandas as pd
import numpy as np
from queue import Queue
from typing import Union, Iterable, List, Tuple
from contextlib import contextmanager
from cranio.utils import random_value_generator, logger, generate_unique_id
from cranio.database import SensorInfo, session_scope, enter_if_not_exists, Document


class SensorError(Exception):
    pass


# TODO: Remove function
def all_from_queue(queue: Union[mp.Queue, Queue]):
    """
    Return a queue.get() generator.

    :param queue: Queue object
    :return: queue.get() generator
    """
    while not queue.empty():
        yield queue.get()


def get_all_from_queue(queue) -> Tuple[List, List]:
    """

    :param queue:
    :return: Index and value arrays as a tuple
    """
    index_arr = []
    value_arr = []
    while not queue.empty():
        index, value = queue.get()
        index_arr.append(index)
        value_arr.append(value)
    return index_arr, value_arr


def datetime_to_seconds(array: Iterable[datetime.datetime], t0: datetime.datetime) -> Iterable[float]:
    """
    Convert datetime to difference in seconds between a reference datetime.

    :param array: Datetime iterable
    :param t0: Reference datetime against which the time difference is calculated
    :return: Float iterable
    """
    # employ conversion to pd.Timestamp for datetime and np.datetime support
    def fun(x): return (pd.Timestamp(x)-t0).total_seconds()
    try:
        return list(map(fun, array))
    except TypeError:
        return fun(array)


@contextmanager
def open_port(port):
    """
    Context manager for opening and closing a port.

    Example:

        >>> with open_port(port):
        >>>     port.do_something()
        >>> # port is closed when leaving the with statement

    :param port:
    :return:
    """
    yield port.open()
    port.close()


def nan_value_generator() -> np.NaN:
    """
    Return a NaN (Not a Number) value.

    :return:
    """
    return np.NaN


class ChannelInfo:
    """ Input channel information. """
    # default string representation
    strfmt = '{self.name} ({self.unit})'
        
    def __init__(self, name: str, unit: str):
        self.name = name
        self.unit = unit
        
    def __str__(self):
        return self.strfmt.format(self=self)


class Sensor:
    """
    Sensor for recording one or more input channels.
    Channels are stored as ChannelInfo objects.
    Open(), close() and read() method must be overloaded.
    """
    # dummy sensor info
    sensor_info = SensorInfo(sensor_serial_number='DUMMY53N50RFTW', turns_in_full_turn=3)
    
    def __init__(self):
        self.channels = []
        self.value_generator = nan_value_generator
    
    def open(self):
        """ Dummy method. """
        pass
    
    def close(self):
        """ Dummy method. """
        pass
    
    def self_test(self) -> bool:
        """
        Self test the sensor by opening and closing the port.

        :return: Boolean indicating whether the self_test was successful or not
        """
        with open_port(self):
            pass
        return True
    
    def register_channel(self, channel_info: ChannelInfo) -> None:
        """
        Register an input channel with the sensor.

        .. note:: Only registered channels are recorded.

        :param channel_info: Channel to be registered
        :return: None
        """
        return self.channels.append(channel_info)
        
    def unregister_channel(self, channel_info: ChannelInfo) -> None:
        """
        Unregister an input channel with the sensor.

        :param channel_info: Channel to be unregistered
        :return: None
        """
        return self.channels.remove(channel_info)
    
    def read(self) -> Tuple[datetime.datetime, dict]:
        """
        Read values from the registered input channels.

        :return: Datetime and value dictionary as a tuple
        """
        if len(self.channels) == 0:
            return None
        values = {}
        for c in self.channels:
            values[str(c)] = self.value_generator()
        # sleep for 10 ms to slow down the sampling
        # if there is no wait between consecutive read() calls,
        # too much data is generated for a plot widget to handle
        time.sleep(0.01)
        return datetime.datetime.now(), values

    @classmethod
    def enter_info_to_database(cls):
        """ Enter copy of self.sensor_info to the database. """
        with session_scope() as s:
            logger.debug(f'Enter sensor info: {str(cls.sensor_info)}')
            enter_if_not_exists(s, cls.sensor_info)


class Producer:
    """ Data producer for recording one or more input sensors. """
        
    def __init__(self):
        self.sensors = []
        self.id = generate_unique_id()
        
    def open(self):
        """ Open all sensor ports. """
        for s in self.sensors:
            s.open()
    
    def close(self):
        """ Close all sensor ports. """
        for s in self.sensors:
            s.close()
        
    def register_sensor(self, sensor: Sensor) -> None:
        """
        Register an input sensor with the producer.

        .. note:: Only registered sensors are recorded.

        :param sensor: Input sensor
        :return: None
        """
        if not sensor.self_test():
            raise SensorError(f'{type(sensor).__name__} did not pass self test')
        self.sensors.append(sensor)
        
    def unregister_sensor(self, sensor: Sensor):
        """
        Unregister an input sensor with the producer.

        :param sensor: Input sensor
        :return: None
        :raises ValueError: if sensor is not registered
        """
        try:
            self.sensors.remove(sensor)
        except ValueError:
            raise ValueError(f'{type(sensor).__name__} is not registered with the producer')
        
    def read(self) -> List[Tuple[datetime.datetime, dict]]:
        """
        Read values from the registered input sensors.

        :return: List of datetime and value dictionary tuples
        """
        return [s.read() for s in self.sensors]


class ProducerProcess:
    """ Process for recording data from a Producer. """
    # default producer class
    producer_class = Producer
    
    def __init__(self, name: str, document: Document):
        self.queue = mp.Queue()
        self.document = document
        self.start_event = mp.Event()
        self.stop_event = mp.Event()
        self.producer = self.producer_class()
        self._process = mp.Process(name=name, target=self.run)
    
    def __str__(self):
        return self.name

    @property
    def name(self) -> str:
        """
        Return the process name.

        :return:
        """
        return self._process.name

    @property
    def sensors(self) -> List[Sensor]:
        return self.producer.sensors

    def is_alive(self) -> bool:
        """
        Return process is_alive status.

        :return: Boolean indicating if the process is running
        """
        return self._process.is_alive()

    def run(self) -> None:
        """
        Open producer ports and start recording data in self.store (DataStore).
        Data is recorded until self.stop_event is triggered.

        :return: None
        """
        # implement required initializations here!
        # open producer
        logger.info('Running producer process "{}"'.format(str(self)))
        with open_port(self.producer):
            while not self.stop_event.is_set():
                if self.start_event.is_set():
                    for index, value_dict in self.producer.read():
                        self.queue.put((index, value_dict))
        logger.info('Stopping producer process "{}"'.format(str(self)))

    def start(self) -> None:
        """
        Start the data producer process. If already running, only the producer is started.

        :return: None
        """
        self.stop_event.clear()
        if not self.is_alive():
            self._process.start()
        self.start_event.set()

    def pause(self) -> None:
        """
        Pause the process. To stop the process, call .join() after .pause().

        :return:
        """
        self.start_event.clear()
        
    def resume(self) -> None:
        """
        Resume the process after pause.

        :return:
        """
        self.start_event.set()
        
    def join(self, timeout=1) -> int:
        """
        Join the process. If the process won't shut down gracefully, it is forcefully terminated.

        :param timeout: Join timeout in seconds
        :return: Process exit code
        """
        self.stop_event.set()
        # close the queue and join the background thread
        #self.queue.close()
        #self.queue.join_thread()
        self._process.join(timeout)
        if self.is_alive():
            logger.error('Producer process "{}" is not shutting down gracefully. '
                          'Resorting to force terminate and join...'.format(str(self)))
            self._process.terminate()
            self._process.join(timeout)
        logger.info('Producer process "{}" joined successfully'.format(str(self)))
        return self._process.exitcode


def create_dummy_sensor() -> Sensor:
    """
    Create a dummy torque (Nm) sensor.

    :return: Sensor object
    """
    logger.debug('Initialize dummy torque sensor')
    sensor = Sensor()
    sensor.value_generator = random_value_generator
    ch = ChannelInfo('torque', 'Nm')
    sensor.register_channel(ch)
    return sensor
