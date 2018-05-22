import os
from contextlib import suppress
from pathlib import Path
from typing import Union


def try_remove(name: Union[str, Path]):
    ''' Try to remove a file from the file system '''
    if name is not None:
        with suppress(PermissionError, FileNotFoundError):
            os.remove(str(name))