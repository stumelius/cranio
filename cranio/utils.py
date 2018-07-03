import os
import logging
import random
from contextlib import suppress
from pathlib import Path
from typing import Union
from ruamel import yaml

DEFAULT_LOGGING_CONFIG_PATH = Path(__file__).parent.parent / 'logging_config.yml'


def try_remove(name: Union[str, Path]):
    ''' Try to remove a file from the file system '''
    if name is not None:
        with suppress(PermissionError, FileNotFoundError):
            os.remove(str(name))


def get_logging_config(path: Union[Path, str]=None) -> dict:
    ''' Return logging configuration dictionary. If path is None, default configuration path is used. '''
    if path is None:
        path = DEFAULT_LOGGING_CONFIG_PATH
    with open(path) as stream:
        return yaml.safe_load(stream)


def get_logging_levels() -> dict:
    ''' Return logging levels as dict {level_priority: level_name} '''
    return logging._levelToName


def level_to_name(level: int) -> str:
    return logging._levelToName[level]


def random_value_generator():
    return random.gauss(0, 1)
