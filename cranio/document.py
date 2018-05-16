'''
DUMMY MODULE
'''
import re
from pathlib import Path
from typing import Union, List, Tuple
DOCUMENT_NAME_TEMPLATE = '{}.json'
DATA_NAME_TEMPLATE = '{}.csv'
LOG_NAME_TEMPLATE = '{}.txt'
ENCODING = 'utf-8'


def extract_name_from_manifest(line):
    pattern = 'MANIFEST\s(\w+)'
    m = re.search(pattern, line)
    return m.group(1)


class FileObject:
    content_type = 'text/plain'

    def __init__(self, path= Union[str, Path]):
        self.path = path
        self.content = None

    def read(self, path: Union[str, Path]) -> str:
        ''' Read from file '''
        with open(str(path), 'r', encoding=ENCODING) as f:
            self.content = f.read()
        return self.content

    def write(self, path: Union[str, Path]) -> None:
        ''' Write to file '''
        self.path = path
        with open(str(self.path), 'w', encoding=ENCODING) as f:
            f.write(self.content)


class Index(FileObject):

    def __init__(self, path: Union[str, Path]):
        super().__init__()
        self.path = path
        self.database_name = None
        self.file_objects = []

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
        raise NotImplementedError

    def load(self):
        ''' Load database from disk '''
        self.index = Index(self.index_path).load()
        return self