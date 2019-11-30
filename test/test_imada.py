import pytest
from cranio.imada import decode_telegram, Imada
from cranio.producer import Sensor
from cranio.model import SensorInfo


def test_decode_telegram():
    assert (-1.234, 'K', 'T', 'O') == decode_telegram('-1.234KTO\r')


@pytest.mark.parametrize('SensorClass', [Imada, Sensor])
def test_imada_and_dummy_sensor_contain_sensor_info_with_serial_number(SensorClass):
    assert type(SensorClass.sensor_info) == SensorInfo
    assert len(SensorClass.sensor_info.sensor_serial_number) > 0
