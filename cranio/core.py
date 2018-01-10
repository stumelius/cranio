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

import pickle
import random

import pandas as pd


class Packet:
    ''' Container for moving data between processes '''
    
    def __init__(self, index, data):
        '''
        Args:
            - index: index values (e.g., time stamps)
            - data: data as a dictionary
        '''
        self.index = index
        self.data = data
        
    def __eq__(self, other):
        return self.index == other.index and self.data == other.data
        
    def encode(self):
        ''' Encodes the Packet as bytes '''
        return pickle.dumps(self)
    
    @classmethod
    def decode(cls, data):
        ''' Decodes bytes back to a Packet object '''
        return pickle.loads(data)
    
    def as_dataframe(self) -> pd.DataFrame:
        ''' Converts the Packet to a pd.DataFrame '''
        return pd.DataFrame(self.data, index=self.index)
    
    @classmethod
    def from_dataframe(cls, df: pd.DataFrame):
        ''' Initializes a Packet from a pd.DataFrame '''
        return cls(index=list(df.index.values), data=df.to_dict(orient='list'))
    
    @classmethod
    def random(cls):
        ''' Creates a Packet with random data '''
        return Packet(index=[random.random()], data={'value': [random.random()]})
    
    @classmethod
    def concat(cls, packets):
        ''' Inefficient concat utilizing pd.concat '''
        return cls.from_dataframe(pd.concat([p.as_dataframe() for p in packets]))
