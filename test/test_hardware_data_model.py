import pytest
from cranio.imada import Imada
from cranio.producer import Sensor
from cranio.model import Document, SensorInfo, DistractorInfo, DistractorType


def test_distractor_table_contains_conversion_factor_for_calculating_distraction_achieved_from_number_of_full_turns(
    database_document_fixture,
):
    document = Document.get_instance()
    document.full_turn_count = 1
    distractor_info = DistractorInfo(
        distractor_type=DistractorType.KLS_ARNAUD, displacement_mm_per_full_turn=1.2
    )
    distraction_achieved_mm = (
        document.full_turn_count * distractor_info.displacement_mm_per_full_turn
    )
    assert distraction_achieved_mm == 1.2


@pytest.mark.parametrize('SensorClass', [Imada, Sensor])
def test_imada_and_dummy_sensor_contain_sensor_info_with_serial_number(SensorClass):
    assert type(SensorClass.sensor_info) == SensorInfo
    assert len(SensorClass.sensor_info.sensor_serial_number) > 0
