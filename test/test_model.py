import pytest
import time
import numpy as np
from sqlalchemy.exc import IntegrityError
from sqlalchemy.inspection import inspect
from cranio.utils import (
    get_logging_levels,
    generate_unique_id,
    utc_datetime,
    logger,
    log_level_to_name,
)
from cranio.model import (
    Patient,
    Session,
    Document,
    Measurement,
    session_scope,
    AnnotatedEvent,
    EventType,
    DistractorInfo,
    DistractorType,
)
from cranio.producer import Sensor


def assert_add_query_and_delete(rows, session, Table):
    primary_key_name = inspect(Table).primary_key[0].name
    # Add rows
    for r in rows:
        session.add(r)
    # Query and verify row insert
    results = session.query(Table).all()
    original_keys = [getattr(r, primary_key_name) for r in rows]
    queried_keys = [getattr(r, primary_key_name) for r in results]
    for key in original_keys:
        assert key in queried_keys
    # Delete rows
    for r in rows:
        session.delete(r)
    # Query and verify deletion
    results = session.query(Table).all()
    queried_keys = [getattr(r, primary_key_name) for r in results]
    for key in original_keys:
        assert key not in queried_keys


def test_create_query_and_delete_patient(database_fixture):
    with session_scope(database_fixture) as s:
        assert_add_query_and_delete(
            [Patient(patient_id=generate_unique_id())], s, Patient
        )


def test_create_query_and_delete_session(database_fixture):
    with session_scope(database_fixture) as s:
        sessions = [Session()]
        assert_add_query_and_delete(sessions, s, Session)


def test_create_query_and_delete_document(database_fixture):
    session = pytest.helpers.add_session(database_fixture)
    patient = pytest.helpers.add_patient(database_fixture)
    sensor_info = pytest.helpers.add_sensor_info(database_fixture)
    with session_scope(database_fixture) as s:
        d = Document(
            session_id=session.session_id,
            patient_id=patient.patient_id,
            sensor_serial_number=sensor_info.sensor_serial_number,
            distractor_type=DistractorType.KLS_RED,
        )
        assert_add_query_and_delete([d], s, Document)


def test_create_query_and_delete_measurement(database_fixture):
    document, *_ = pytest.helpers.add_document_and_foreign_keys(database_fixture)
    with session_scope(database_fixture) as s:
        measurements = [
            Measurement(
                time_s=t, torque_Nm=np.random.rand(), document_id=document.document_id
            )
            for t in range(10)
        ]
        assert_add_query_and_delete(measurements, s, Measurement)


def test_database_init_populate_lookup_tables(database_fixture):
    with session_scope(database_fixture) as s:
        # Event types
        event_types = s.query(EventType).all()
        targets = EventType.event_types()
        assert len(event_types) == len(targets)
        for real, target in zip(event_types, targets):
            assert real.event_type == target.event_type
            assert real.event_type_description == target.event_type_description
        # Distractor types
        distractor_infos = s.query(DistractorInfo).all()
        assert len(distractor_infos) == len(DistractorInfo.distractor_infos())
        distractor_types = [d.distractor_type for d in distractor_infos]
        assert DistractorType.KLS_ARNAUD in distractor_types
        assert DistractorType.KLS_RED in distractor_types


def test_create_query_and_delete_annotated_event(database_fixture):
    document, *_ = pytest.helpers.add_document_and_foreign_keys(database_fixture)
    with session_scope(database_fixture) as s:
        events = [
            AnnotatedEvent(
                event_type=EventType.distraction_event_type().event_type,
                event_num=i,
                document_id=document.document_id,
                annotation_done=False,
                recorded=True,
            )
            for i in range(10)
        ]
        assert_add_query_and_delete(events, s, AnnotatedEvent)


@pytest.mark.skip('FIXME: IntegrityError is raised after add')
def test_annotated_event_foreign_key_constraint(database_fixture):
    with session_scope(database_fixture) as s:
        with pytest.raises(IntegrityError):
            s.add(
                AnnotatedEvent(
                    event_type=EventType.distraction_event_type().event_type,
                    event_num=1,
                    document_id=1337,
                )
            )


def test_get_time_series_related_to_document(database_fixture):
    document, *_ = pytest.helpers.add_document_and_foreign_keys(database_fixture)
    # Generate data and associate with document
    n = 100
    x_arr = np.linspace(0, 1, n)
    y_arr = np.random.rand(n)
    measurements = [
        Measurement(document_id=document.document_id, time_s=x, torque_Nm=y)
        for x, y in zip(x_arr, y_arr)
    ]
    database_fixture.bulk_insert(measurements)
    x, y = document.get_related_time_series(database_fixture)
    np.testing.assert_array_almost_equal(x, x_arr)
    np.testing.assert_array_almost_equal(y, y_arr)


def test_get_non_existing_time_series_related_to_document(database_fixture):
    document, *_ = pytest.helpers.add_document_and_foreign_keys(database_fixture)
    x, y = document.get_related_time_series(database_fixture)
    assert len(x) == 0 and len(y) == 0


def test_enter_if_not_exists(database_fixture):
    document, *_ = pytest.helpers.add_document_and_foreign_keys(database_fixture)
    for _ in range(10):
        database_fixture.insert(document, insert_if_exists=False)
    with session_scope(database_fixture) as s:
        n = (
            s.query(Document)
            .filter(Document.document_id == document.document_id)
            .count()
        )
    assert n == 1


def test_document_get_related_events_count_is_correct(database_fixture):
    document, *_ = pytest.helpers.add_document_and_foreign_keys(database_fixture)
    n = 10
    annotated_events = [
        AnnotatedEvent(
            event_type=EventType.distraction_event_type().event_type,
            event_num=i,
            document_id=document.document_id,
            annotation_done=False,
            recorded=True,
        )
        for i in range(n)
    ]
    database_fixture.bulk_insert(annotated_events)
    assert len(document.get_related_events(database_fixture)) == n


def test_measurement_as_dict_returns_only_table_columns():
    m = Measurement(measurement_id=1, document_id=1, time_s=1, torque_Nm=1)
    d = m.as_dict()
    cols = ('measurement_id', 'document_id', 'time_s', 'torque_Nm')
    assert len(d) == len(cols)
    for col in cols:
        assert col in d


def test_measurement_copy_returns_new_instance_with_same_attributes():
    m1 = Measurement(measurement_id=1, document_id=1, time_s=1, torque_Nm=1)
    m2 = m1.copy()
    assert m2.as_dict() == m1.as_dict()
    assert m1 != m2


def test_distractor_info_takes_distractor_type_and_displacement_mm_per_full_turn_as_args():
    DistractorInfo(distractor_type='KLS Arnaud', displacement_mm_per_full_turn=1.15)
