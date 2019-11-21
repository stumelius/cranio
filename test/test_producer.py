import numpy as np
import datetime
from cranio.producer import datetime_to_seconds, create_dummy_sensor, Sensor


def test_datetime_to_seconds():
    t0 = datetime.datetime.utcnow()
    for arr in (
        datetime.datetime.utcnow(),
        [datetime.datetime.utcnow()],
        np.datetime64('2017-12-18T17:13:45.351738000'),
        [np.datetime64('2017-12-18T17:13:45.351738000')],
    ):
        datetime_to_seconds(arr, t0)


def test_create_dummy_sensor_returns_sensor():
    assert type(create_dummy_sensor()) == Sensor
