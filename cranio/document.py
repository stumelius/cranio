'''
DUMMY MODULE
'''
import re
from contextlib import suppress
from pathlib import Path
from typing import Union, List, Tuple
DOCUMENT_NAME_TEMPLATE = '{}.json'
DATA_NAME_TEMPLATE = '{}.csv'
LOG_NAME_TEMPLATE = '{}.txt'
ENCODING = 'utf-8'

class NoChangesToCommitError(Exception):
    pass


def extract_name_from_manifest(line):
    pattern = 'MANIFEST\s(\w+)'
    m = re.search(pattern, line)
    return m.group(1)


class FileObject:
    ''' Content is read when needed '''
    content_type = 'text/plain'

    def __init__(self, path: Union[str, Path]=None):
        self.path = path
        self._content = None
        # original content
        self.__content = None

    @property
    def content(self):
        if self._content is None:
            self.read(self.path)
        return self._content

    @content.setter
    def content(self, value):
        self._content = value

    def read(self, path: Union[str, Path]=None) -> str:
        ''' Read from file '''
        if path is None:
            path = self.path
        with open(str(path), 'r', encoding=ENCODING) as f:
            self.content = f.read()
            self.__content = self.content
        return self.content

    def write(self, path: Union[str, Path]=None) -> None:
        '''
        Write to file.

        Raises:
             NoChangesToCommitError: No changes to commit to {path}
        '''
        if path is None:
            path = self.path
        if self._content != self.__content and path == self.path:
            self.path = path
            with open(str(self.path), 'w', encoding=ENCODING) as f:
                f.write(self.content)
        else:
            raise NoChangesToCommitError(f'No changes to commit to {path}')


class Index(FileObject):

    def __init__(self, path: Union[str, Path]):
        super().__init__(path)
        self.database_name = None
        self.file_objects = []

    def __iter__(self):
        return iter(self.file_objects)

    def __len__(self):
        return len(self.file_objects)

    def __getitem__(self, key):
        return self.file_objects[key]

    def load(self):
        ''' Load index from disk '''
        self.database_name, self.file_objects = self.parse(self.read(self.path))
        return self

    @classmethod
    def parse(cls, index_str: str) -> Tuple[str, List[FileObject]]:
        '''
        Index/manifest string format:

        MANIFEST <database_name>
        <content_type>: <path_to_file>
        .
        .
        .
        <content_type>: <path_to_file>
        '''
        file_objects = []
        for i, line in enumerate(index_str.splitlines()):
            if i == 0:
                database_name = extract_name_from_manifest(line)
                continue
            content_type, path = (x.strip() for x in line.split(':'))
            file_object = FileObject(path)
            file_object.content_type = content_type
            file_objects.append(file_object)
        return database_name, file_objects


class FlatfileDatabase:
    ''' Simple flat file database '''
    index_name = 'db.manifest'

    def __init__(self, index_path: Union[str, Path]):
        self.index_path = index_path
        self.index = None

    def commit(self):
        ''' Commit all changes to disk '''
        for file_object in self.index:
            # TODO: what if a write fails? changes are lost and/or data gets corrupted
            # write to a temporary file
            # if any of the writes fail, fallback
            with suppress(NoChangesToCommitError):
                file_object.write()



    def load(self):
        ''' Load database from disk '''
        self.index = Index(self.index_path).load()
        return self
