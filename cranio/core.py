'''
Implements a serializable Packet object for data transfer over separate processes

Copyright (C) 2017  Simo Tumelius

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''
import uuid
import pickle
import random
import pandas as pd
from typing import Tuple, List
from datetime import datetime


def generate_unique_id():
    """

    :return: Unique id based on host ID, sequence number and current time
    """
    return str(uuid.uuid1())


def timestamp():
    """

    :return: Current date and time (UTC+0)
    """
    return datetime.utcnow()


class Packet:
    """ Data transfer unit between processes. """
    
    def __init__(self, index, data: dict):
        """

        :param index: Index values (e.g., time stamps)
        :param data: Data dictionary
        """
        self.index = index
        self.data = data
        
    def __eq__(self, other) -> bool:
        """

        :param other:
        :return:
        """
        return self.index == other.index and self.data == other.data
        
    def encode(self):
        """
        Encode the packet as a pickled bytes literal.

        :return: Bytes literal
        """
        return pickle.dumps(self)
    
    @classmethod
    def decode(cls, data):
        """
        Decode a pickled bytes literal as a packet.

        :param data: Bytes literal
        :return: Packet object
        """
        return pickle.loads(data)
    
    def as_dataframe(self) -> pd.DataFrame:
        """
        Convert to a pandas DataFrame.

        :return:
        """
        return pd.DataFrame(self.data, index=self.index)
    
    def as_tuple(self) -> Tuple[List, dict]:
        """
        Convert to a (index, data_dict) tuple.

        :return:
        """
        return self.index, self.data
    
    @classmethod
    def from_dataframe(cls, df: pd.DataFrame):
        """
        Initialize from a pandas DataFrame.

        :param df:
        :return: Packet object
        """
        return cls(index=list(df.index.values), data=df.to_dict(orient='list'))
    
    @classmethod
    def random(cls):
        """
        Initialize with random index and data.

        :return: Randomized Packet object
        """
        return Packet(index=[random.random()], data={'value': [random.random()]})
    
    @classmethod
    def concat(cls, packets: List):
        """
        Concatenate multiple packets in a single packet.

        :param packets: List of Packet objects
        :return: Packet object
        """

        return cls.from_dataframe(pd.concat([p.as_dataframe() for p in packets]))
