import pytest
from cranio.app.widget import MetaDataWidget


@pytest.fixture(scope='function')
def meta_data_widget(database_fixture):
    widget = MetaDataWidget(database=database_fixture)
    return widget


def test_meta_data_widget_stores_active_operator_as_str(meta_data_widget):
    meta_data_widget.active_operator = 123
    assert meta_data_widget.active_operator == '123'
