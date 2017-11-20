import pickle
import random
import pandas as pd

class Packet:
    
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
        return pickle.dumps(self)
    
    @classmethod
    def decode(cls, data):
        return pickle.loads(data)
    
    def as_dataframe(self):
        return pd.DataFrame(self.data, index=self.index)
    
    @classmethod
    def from_dataframe(cls, df):
        return cls(index=list(df.index.values), data=df.to_dict(orient='list'))
    
    @classmethod
    def random(cls):
        return Packet(index=[random.random()], data={'value': [random.random()]})