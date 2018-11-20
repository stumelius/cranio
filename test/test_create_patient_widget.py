import pytest
from cranio.app.widget import PatientWidget
from sqlalchemy.exc import IntegrityError


def test_add_patient(database_fixture):
    widget = PatientWidget(database=database_fixture)
    for i, name in enumerate(('foo', 'bar', 'baz')):
        widget.add_patient(name)
        assert widget.patient_count() == i+1


def test_add_patient_already_exists(database_fixture):
    widget = PatientWidget(database=database_fixture)
    widget.add_patient('foo bar')
    with pytest.raises(IntegrityError):
        widget.add_patient('foo bar')


def test_add_patient_empty_string(database_fixture):
    widget = PatientWidget(database=database_fixture)
    with pytest.raises(IntegrityError):
        widget.add_patient('')
