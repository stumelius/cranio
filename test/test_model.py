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
    Log,
    LogLevel,
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


def test_create_query_and_delete_document(database_patient_fixture):
    Sensor.enter_info_to_database(database_patient_fixture)
    with session_scope(database_patient_fixture) as s:
        d = Document(
            session_id=Session.get_instance().session_id,
            patient_id=Patient.get_instance().patient_id,
            sensor_serial_number=Sensor.sensor_info.sensor_serial_number,
            distractor_type=DistractorType.KLS_RED,
        )
        assert_add_query_and_delete([d], s, Document)


def test_create_query_and_delete_measurement(database_document_fixture):
    with session_scope(database_document_fixture) as s:
        measurements = [
            Measurement(
                time_s=t,
                torque_Nm=np.random.rand(),
                document_id=Document.get_instance().document_id,
            )
            for t in range(10)
        ]
        assert_add_query_and_delete(measurements, s, Measurement)


def test_create_query_and_delete_log(database_fixture):
    with session_scope(database_fixture) as s:
        # create log for all logging levels
        logs = []
        for i, level in enumerate(get_logging_levels().keys()):
            log = Log(
                created_at=utc_datetime(),
                level=level,
                message=i,
                session_id=Session.get_instance().session_id,
                trace='Empty',
                logger='test.logger',
            )
            logs.append(log)
        assert_add_query_and_delete(logs, s, Log)


@pytest.mark.skip('FIXME: IntegrityError is raised after add')
def test_add_log_with_invalid_level(database_fixture):
    log = Log(
        created_at=utc_datetime(),
        level=1337,
        message='foo',
        session_id=Session.get_instance().session_id,
        trace='Empty',
        logger='test.logger',
    )
    with pytest.raises(IntegrityError):
        database_fixture.insert(log)


def test_database_init_populate_lookup_tables(database_fixture):
    logging_levels = get_logging_levels()
    with session_scope(database_fixture) as s:
        # Log levels
        levels = s.query(LogLevel).all()
        assert len(levels) == len(logging_levels)
        for log_level in s.query(LogLevel).all():
            assert log_level.level in logging_levels.keys()
            assert log_level.level_name in logging_levels.values()
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


def test_create_query_and_delete_annotated_event(database_document_fixture):
    doc_id = Document.get_instance().document_id
    with session_scope(database_document_fixture) as s:
        events = [
            AnnotatedEvent(
                event_type=EventType.distraction_event_type().event_type,
                event_num=i,
                document_id=doc_id,
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


def test_get_time_series_related_to_document(database_document_fixture):
    # Generate data and associate with document
    n = 100
    document = Document.get_instance()
    x_arr = np.linspace(0, 1, n)
    y_arr = np.random.rand(n)
    measurements = [
        Measurement(document_id=document.document_id, time_s=x, torque_Nm=y)
        for x, y in zip(x_arr, y_arr)
    ]
    database_document_fixture.bulk_insert(measurements)
    x, y = document.get_related_time_series(database_document_fixture)
    np.testing.assert_array_almost_equal(x, x_arr)
    np.testing.assert_array_almost_equal(y, y_arr)


def test_get_non_existing_time_series_related_to_document(database_document_fixture):
    document = Document.get_instance()
    x, y = document.get_related_time_series(database_document_fixture)
    assert len(x) == 0 and len(y) == 0


def test_document_has_sensor_serial_number_column():
    document = Document()
    assert hasattr(document, 'sensor_serial_number')


def test_enter_if_not_exists(database_document_fixture):
    document = Document.get_instance()
    for _ in range(10):
        database_document_fixture.insert(document, insert_if_exists=False)
    with session_scope(database_document_fixture) as s:
        n = (
            s.query(Document)
            .filter(Document.document_id == document.document_id)
            .count()
        )
    assert n == 1


def test_document_get_related_events_count_is_correct(database_document_fixture):
    document = Document.get_instance()
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
    database_document_fixture.bulk_insert(annotated_events)
    assert len(document.get_related_events(database_document_fixture)) == n


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


def test_session_continue_from_sets_session_instance(database_fixture):
    # Create new session
    s2 = Session()
    database_fixture.insert(s2)
    Session.continue_from(s2)
    assert Session.get_instance() == s2


def test_logging_is_directed_to_database_log_table_with_correct_values(
    database_fixture,
):
    wait_duration = 0.01  # seconds
    t_start = utc_datetime()
    # short wait to ensure that t_start < log timestamp
    time.sleep(wait_duration)
    msg = 'This should not raise an IntegrityError'
    logger.info(msg)
    # short wait to ensure that t_stop > log timestamp
    time.sleep(wait_duration)
    t_stop = utc_datetime()
    with session_scope(database_fixture) as s:
        logs = s.query(Log).filter(Log.message == msg).all()
        assert len(logs) == 1
        log = logs[0]
        assert log.session_id == Session.get_instance().session_id
        assert log.logger == logger.name
        assert log_level_to_name(log.level).lower() == 'info'
        # verify that the log entry is created between t_start and current time
        assert t_start <= log.created_at <= t_stop
