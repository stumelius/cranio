import pytest
import random
from cranio.core import Packet

@pytest.fixture
def packet_integer():
    index = [0] * 10
    data_dict = {'value': [random.randint(0,100)]*len(index)}
    return Packet(index, data_dict)

@pytest.fixture
def packet_float():
    index = [0] * 10
    data_dict = {'value': [random.random()]*len(index)}
    return Packet(index, data_dict)

@pytest.fixture
def packets(packet_integer, packet_float):
    return (packet_integer, packet_float)


def test_packet_encode_and_decode(packets):
    for p in packets:
        decoded = p.decode(p.encode())
        assert decoded == p
        
def test_packet_as_and_from_dataframe(packets):
    for p in packets:
        df = p.as_dataframe()
        assert list(df.index.values) == list(p.index)
        assert df.to_dict(orient='list') == p.data
        p1 = Packet.from_dataframe(df)
        assert p == p1