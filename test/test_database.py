import pytest
import os
import copy
from typing import Union
from contextlib import suppress
from cranio.document import FlatfileDatabase, FileObject, Index, ENCODING
from pathlib import Path

DATABASE_NAME = 'foo'


def try_remove(name: Union[str, Path]):
    ''' Try to remove a file from the file system '''
    if name is not None:
        with suppress(PermissionError, FileNotFoundError):
            os.remove(str(name))


@pytest.fixture
def txt_path():
    content = 'foo bar'
    path = 'foo.txt'
    with open(path, 'w', encoding=ENCODING) as f:
        f.write(content)
    yield path
    try_remove(path)


@pytest.fixture
def csv_path():
    content = 'foo;bar'
    path = 'foo.csv'
    with open(path, 'w', encoding=ENCODING) as f:
        f.write(content)
    yield path
    try_remove(path)


@pytest.fixture
def index_path(txt_path, csv_path):
    content = '\n'.join(['MANIFEST ' + DATABASE_NAME,
                         'text/plain: ' + txt_path,
                         'text/csv: ' + csv_path])
    path = FlatfileDatabase.index_name
    with open(path, 'w', encoding=ENCODING) as f:
        f.write(content)
    yield path
    try_remove(path)


def test_FileObject_read_and_write(txt_path):
    path = txt_path
    f = FileObject()
    assert f.content is None
    f.read(path)
    assert f.content is not None
    content = copy.copy(f.content)
    name = 'foo.txt'
    # write to file
    f.write(name)
    # read and verify content
    assert f.read(name) == content
    try_remove(name)


def assert_default_index(index):
    assert index.database_name == DATABASE_NAME
    assert len(index.file_objects) == 2
    assert index.file_objects[0].content_type == 'text/plain'
    assert index.file_objects[1].content_type == 'text/csv'


def test_Index_load(index_path):
    index = Index(index_path).load()
    assert_default_index(index)


def test_FileDatabase_load(index_path):
    db = FlatfileDatabase(index_path).load()
    assert_default_index(db.index)


