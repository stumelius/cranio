import pytest
from cranio.app.widget import MetaDataWidget


@pytest.fixture(scope='function')
def meta_data_widget(database_fixture):
    widget = MetaDataWidget(database=database_fixture)
    return widget


def test_meta_data_widget_stores_active_operator_as_str(meta_data_widget):
    meta_data_widget.operator = 123
    assert meta_data_widget.operator == '123'


def test_meta_data_widget_patient_cannot_be_edited(meta_data_widget):
    assert not meta_data_widget.patient_widget.isEnabled()
