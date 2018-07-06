"""
.. todo:: Combine with the core module
"""
import os
import time
import logging
import random
from contextlib import suppress
from pathlib import Path
from typing import Union, Dict
from ruamel import yaml

DEFAULT_LOGGING_CONFIG_PATH = Path(__file__).parent.parent / 'logging_config.yml'


class UTCFormatter(logging.Formatter):
    """ Logging formatter that converts timestamps to UTC+0. """
    converter = time.gmtime


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
