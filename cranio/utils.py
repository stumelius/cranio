"""
Utility functions and classes.
"""
import os
import sys
import time
import logging
import logging.config
import random
import uuid
from datetime import datetime
from contextlib import suppress
from pathlib import Path
from typing import Union, Dict
from ruamel import yaml
from PyQt5.QtCore import QStateMachine
from cranio.constants import DEFAULT_LOGGING_CONFIG_PATH


class CustomAdapter(logging.LoggerAdapter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.machine = None
        self.database = None

    @property
    def name(self):
        return self.logger.name

    def process(self, msg, kwargs):
        # Add state context
        if not self.machine:
            self.extra['state'] = 'UnknownState'
        else:
            try:
                self.extra['state'] = str(self.machine.current_state())
            except ValueError:
                self.extra['state'] = 'UndefinedState'
        # Add database context
        self.extra['database'] = self.database
        return super().process(msg, kwargs)

    def register_machine(self, machine: QStateMachine):
        logger.debug(f'{machine} registered with logging adapter')
        self.machine = machine

    def register_database(self, database):
        logger.debug(f'Database {database.url} registered with logging adapter')
        self.database = database

    def unregister_database(self, database):
        if database != self.database:
            raise ValueError(
                f'Database {database.url} not registered with logging adapter'
            )
        logger.debug(f'Database {self.database.url} unregistered with logging adapter')
        self.database = None


logger = CustomAdapter(logging.getLogger('cranio'), {})


class UTCFormatter(logging.Formatter):
    """ Logging formatter that converts timestamps to UTC+0. """

    converter = time.gmtime


def generate_unique_id():
    """

    :return: Unique id based on host ID, sequence number and current time
    """
    return str(uuid.uuid1())


def utc_datetime():
    """

    :return: Current date and time (UTC+0)
    """
    return datetime.utcnow()


def try_remove(name: Union[str, Path]):
    """ Try and remove a file from the filesystem. """
    if name is not None:
        with suppress(PermissionError, FileNotFoundError):
            os.remove(str(name))


def get_logging_config(path: Union[Path, str] = None) -> dict:
    """
    Return logging configuration dictionary. If path is None, default configuration path is used.

    :param path: Logging configuration file path. If None, default configuration path is returned.
    :return: Logging configuration in a dictionary
    """
    if path is None:
        path = DEFAULT_LOGGING_CONFIG_PATH
    with open(path) as stream:
        return yaml.safe_load(stream)


def configure_logging(log_level: str = 'INFO'):
    d = get_logging_config()
    logging.config.dictConfig(d)
    logger.setLevel(log_level)


def get_logging_levels() -> Dict[int, str]:
    """
    Return logging level dictionary.

    :return: Dictionary {level_priority: level_name}
    """
    return logging._levelToName


def log_level_to_name(level: int) -> str:
    """
    Convert log level value to log level name.

    Example:
        >>> print(log_level_to_name(0))
        NOTSET

    :param level: Log level value
    :return: Log level name
    """
    return logging._levelToName[level]


def random_value_generator() -> float:
    """ Generate a random value. """
    return random.gauss(0, 1)


def default_excepthook(exctype: Exception, value: str, tb):
    """
    Global function to catch unhandled exceptions.

    :param exctype:
    :param value:
    :param tb:
    :return:
    """
    logging.exception(
        f'UNHANDLED {exctype.__name__}: {value}', exc_info=(exctype, value, tb)
    )
    sys.__excepthook__(exctype, value, tb)


def attach_excepthook(excepthook=None):
    if excepthook is None:
        excepthook = default_excepthook
    sys.excepthook = excepthook


def utc_offset() -> float:
    """
    Return UTC offset of local time.

    :return:
    """
    offset = time.timezone if (time.localtime().tm_isdst == 0) else time.altzone
    return offset / 60 / 60 * (-1)
