import pytest
import random
import time
import pandas as pd
from cranio.producer import ChannelInfo, Sensor, Producer, get_all_from_queue


def random_value_generator():
    return random.gauss(0, 1)


def test_channel_info():
    c = ChannelInfo('torque', 'Nm')
    assert str(c) == 'torque (Nm)'


def test_sensor():
    s = Sensor()
    assert s.self_test()
    assert s.read() is None
    ch = ChannelInfo('torque', 'Nm')
    s.register_channel(ch)
    index, value_dict = s.read()
    assert len(value_dict) > 0
    assert list(value_dict) == [str(ch)]


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


def test_producer_process_start_and_join(producer_process, database_document_fixture):
    p = producer_process
    p.start()
    assert p.is_alive()
    time.sleep(1)
    assert p.is_alive()
    p.pause()
    assert p.is_alive()
    p.start()
    assert p.is_alive()
    p.pause()
    # Read values from queue
    index_arr, value_arr = get_all_from_queue(p.queue)
    # No sensors -> empty data
    assert len(index_arr) == 0


def test_producer_process_with_sensors(producer_process, database_document_fixture):
    p = producer_process
    s = Sensor()
    s.value_generator = random_value_generator
    channels = [ChannelInfo('torque', 'Nm'), ChannelInfo('load', 'N'), ChannelInfo('extension', 'mm')]
    for c in channels:
        s.register_channel(c)
    p.producer.register_sensor(s)
    p.start()
    assert p.is_alive()
    # Record for 2 seconds
    time.sleep(2)
    p.pause()
    # Read values from queue
    index_arr, value_arr = get_all_from_queue(p.queue)
    # Convert value_arr (list of dicts) to a DataFrame
    df = pd.DataFrame(value_arr, index=index_arr)
    for c in channels:
        assert str(c) in df
