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
from cranio.constants import DEFAULT_LOGGING_CONFIG_PATH

logger = logging.getLogger('cranio')


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


def get_logging_config(path: Union[Path, str]=None) -> dict:
    """
    Return logging configuration dictionary. If path is None, default configuration path is used.

    :param path: Logging configuration file path. If None, default configuration path is returned.
    :return: Logging configuration in a dictionary
    """
    if path is None:
        path = DEFAULT_LOGGING_CONFIG_PATH
    with open(path) as stream:
        return yaml.safe_load(stream)


def configure_logging():
    # logging configuration
    d = get_logging_config()
    logging.config.dictConfig(d)


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
    logging.exception(f'UNHANDLED {exctype.__name__}: {value}', exc_info=(exctype, value, tb))
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
