import pytest
import random
import time
import multiprocessing as mp
from daqstore.store import DataStore
from cranio.producer import ChannelInfo, Sensor, Producer, ProducerProcess


def random_value_generator():
    return random.gauss(0, 1)


def test_channel_info():
    c = ChannelInfo('torque', 'Nm')
    assert str(c) == 'torque (Nm)'


def test_sensor():
    s = Sensor()
    assert s.self_test()
    assert s.read() == None
    ch = ChannelInfo('torque', 'Nm')
    s.register_channel(ch)
    packet = s.read()
    df = packet.as_dataframe()
    assert not df.empty
    assert list(df.columns) == [str(ch)]


def test_producer_add_and_remove_sensors():
    n = 3
    p = Producer()
    sensors = [Sensor() for _ in range(n)]
    for s in sensors:
        p.register_sensor(s)
    assert len(p.sensors) == n
    for s in sensors:
        p.unregister_sensor(s)
    assert len(p.sensors) == 0


def test_producer_process_start_and_join(data_store, database_document_fixture):
    p = ProducerProcess('test_process', data_store)
    p.start()
    assert p.is_alive()
    time.sleep(1)
    assert p.is_alive()
    p.pause()
    assert p.is_alive()
    p.start()
    assert p.is_alive()
    p.pause()
    # read and flush store
    data_store.read()
    data_store.flush()
    # no sensors -> empty data
    df = p.read(include_cache=True)
    assert df.empty
    p.join()
    assert not p.is_alive()


def test_producer_process_with_sensors(data_store, database_document_fixture):
    p = ProducerProcess('test_process', data_store)
    s = Sensor()
    s._default_value_generator = random_value_generator
    channels = [ChannelInfo('torque', 'Nm'), ChannelInfo('load', 'N'), ChannelInfo('extension', 'mm')]
    for c in channels:
        s.register_channel(c)
    p.producer.register_sensor(s)
    p.start()
    assert p.is_alive()
    time.sleep(1)
    p.pause()
    # read and flush store
    data_store.read()
    data_store.flush()
    df = p.read(include_cache=True)
    for c in channels:
        assert str(c) in df
    p.join()
    assert not p.is_alive()