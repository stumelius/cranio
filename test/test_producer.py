import numpy as np
import datetime
from cranio.producer import datetime_to_seconds, ProducerProcess, plug_dummy_sensor


def test_datetime_to_seconds():
    t0 = datetime.datetime.utcnow()
    for arr in (datetime.datetime.utcnow(), [datetime.datetime.utcnow()], 
                np.datetime64('2017-12-18T17:13:45.351738000'), [np.datetime64('2017-12-18T17:13:45.351738000')]):
        datetime_to_seconds(arr, t0)


def test_only_dummy_sensor_is_plugged_by_plug_dummy_sensor(data_store, database_fixture):
    process = ProducerProcess(name='dummy', store=data_store)
    sensor = plug_dummy_sensor(process)
    assert len(process.producer.sensors) == 1
    assert process.producer.sensors[0] == sensor
