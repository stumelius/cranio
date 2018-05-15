'''
DUMMY MODULE
'''
from pathlib import Path
from typing import Union, List
DOCUMENT_NAME_TEMPLATE = '{}.json'
DATA_NAME_TEMPLATE = '{}.csv'
LOG_NAME_TEMPLATE = '{}.txt'

ENCODING = 'utf-8'


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
        self.file_objects = []

    def load(self):
        ''' Load index from disk '''
        self.file_objects = self.parse(self.read(self.path))
        return self

    @classmethod
    def parse(cls, index_str: str) -> List[FileObject]:
        ''' Index string format: "content_type: path_to_file" '''
        file_objects = []
        for line in index_str.splitlines():
            content_type, path = (x.strip() for x in line.split(':'))
            file_object = FileObject(path)
            file_object.content_type = content_type
            file_objects.append(file_object)
        return file_objects


class FileDatabase:
    ''' Simple file database '''
    index_name = 'index'

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