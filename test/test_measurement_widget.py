import pytest
from cranio.app.widget import MeasurementWidget


@pytest.fixture
def measurement_widget():
    widget = MeasurementWidget()
    yield widget


def test_distractor_widget_value_is_one_by_default(measurement_widget):
    assert measurement_widget.distractor_widget.value == 1


def test_clicking_distractor_widget_up_increases_value_by_one(measurement_widget):
    measurement_widget.distractor_widget.step_up()
    assert measurement_widget.distractor_widget.value == 2


def test_clicking_distractor_widget_down_decreases_value_by_one(measurement_widget):
    measurement_widget.distractor_widget.value = 2
    measurement_widget.distractor_widget.step_down()
    assert measurement_widget.distractor_widget.value == 1


def test_distractor_widget_down_has_no_effect_when_distractor_is_one(measurement_widget):
    measurement_widget.distractor_widget.step_down()
    assert measurement_widget.distractor_widget.value == 1


def test_distractor_widget_up_has_no_effect_when_distractor_is_ten(measurement_widget):
    measurement_widget.distractor_widget.value = 10
    measurement_widget.distractor_widget.step_up()
    assert measurement_widget.distractor_widget.value == 10

