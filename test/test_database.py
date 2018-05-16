import pytest
import os
import copy
from typing import Union
from contextlib import suppress
from cranio.document import FlatfileDatabase, FileObject, Index, ENCODING, NoChangesToCommitError
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


def test_FileObject_read_modify_and_write(txt_path):
    path = txt_path
    f = FileObject()
    # no path defined yet
    with pytest.raises(FileNotFoundError):
        f.content
    f.path = path
    # content is read when property is accessed
    assert f.content is not None
    content = f.content + ' baz'
    # try write to file without making any changes
    with pytest.raises(NoChangesToCommitError):
        f.write()
    # make changes and write
    f.content = content
    f.write()
    # read and verify content
    assert f.read() == content
    try_remove(path)


def assert_default_index(index):
    assert index.database_name == DATABASE_NAME
    assert len(index.file_objects) == 2
    assert index.file_objects[0].content_type == 'text/plain'
    assert index.file_objects[1].content_type == 'text/csv'


def test_Index_load(index_path):
    index = Index(index_path).load()
    assert_default_index(index)


def test_FileDatabase_load_modify_and_commit(index_path):
    db = FlatfileDatabase(index_path).load()
    assert_default_index(db.index)
    # modify text file
    txt_file = db.index[0]
    txt_file.content += ' baz'
    db.commit()
    # verify that the changes were committed
    new_txt_file = FileObject(txt_file.path)
    assert new_txt_file.content == txt_file.content



