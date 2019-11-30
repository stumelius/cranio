"""
Relational database definitions and classes/functions for database management.
"""
from typing import Tuple, List, Iterable
from contextlib import contextmanager, closing
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import URL, make_url
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Numeric,
    Boolean,
    ForeignKey,
    create_engine,
    CheckConstraint,
    event,
    Table,
)
from cranio.utils import generate_unique_id, utc_datetime, logger
from cranio import __version__
from cranio.constants import SQLITE_FILENAME


class Database:
    def __init__(
        self,
        drivername: str,
        username: str = None,
        password: str = None,
        host: str = None,
        port: int = None,
        database: str = None,
    ):
        self.url = URL(drivername, username, password, host, port, database)
        self.engine = None
        self.initialized = False

    @classmethod
    def from_str(cls, url_str: str):
        url = make_url(url_str)
        connect_args = {
            'drivername': url.drivername,
            'username': url.username,
            'password': url.password,
            'host': url.host,
            'port': url.port,
            'database': url.database,
        }
        return cls(**connect_args)

    def create_engine(self) -> Engine:
        """
        Initialize a database connection and return the database engine.

        :return:
        """
        logger.info(f'Initialize database {self.url}')
        self.engine = create_engine(self.url)
        # Enforce sqlite foreign keys
        event.listen(self.engine, 'connect', _fk_pragma_on_connect)
        return self.engine

    def populate_lookup_tables(self):
        logger.info(f'Populate lookup tables in {self.url}')
        with session_scope(self) as s:
            for event_type in EventType.event_types():
                enter_if_not_exists(s, event_type)
            for distractor_info in DistractorInfo.distractor_infos():
                enter_if_not_exists(s, distractor_info)

    def init(self):
        """
        Create declarative tables and populate lookup tables.
        :return:
        """
        logger.info(f'Create declarative tables in {self.url}')
        Base.metadata.create_all(self.engine)
        self.populate_lookup_tables()
        self.initialized = True

    def session_scope(self):
        return session_scope(self)

    def insert(self, row: Table, insert_if_exists: bool = True) -> Table:
        """
        Insert row to the database.

        :param row:
        :param insert_if_exists:
        :return: Inserted row
        """
        with session_scope(self) as s:
            if insert_if_exists:
                s.add(row)
            else:
                s.merge(row)
        return row

    def bulk_insert(self, rows: Iterable[Table]) -> List[Table]:
        """
        Batch insert as a single transaction.

        :param rows:
        :return:
        """
        with session_scope(self) as s:
            for row in rows:
                s.add(row)
        return rows

    def clear(self) -> None:
        """
        Truncate all database tables.

        .. todo:: Needs to be tested!

        :return: None
        """
        logger.info(f'Clear database {self.url}')
        with closing(self.engine.connect()) as con:
            trans = con.begin()
            for table in reversed(Base.metadata.sorted_tables):
                con.execute(table.delete())
            trans.commit()


class DefaultDatabase:
    SQLITE = Database('sqlite', None, None, None, None, SQLITE_FILENAME)


Base = declarative_base()
# Disable expiry on commit to prevent detachment of database objects (#91)
SQLSession = sessionmaker(expire_on_commit=False)


def _fk_pragma_on_connect(dbapi_con, con_record):
    """
    Enforce sqlite foreign key constraints.

    :param dbapi_con:
    :param con_record:
    :return:
    """
    dbapi_con.execute('pragma foreign_keys=ON')


def enter_if_not_exists(session: SQLSession, row: Base):
    """
    Enter row to database if it doesn't already exist.

    :param session:
    :param row:
    :return:
    """
    session.merge(row)


@contextmanager
def session_scope(database: Database):
    """
    Provide a transactional scope around a series of operations.

    :param database: Database (DefaultDatabase.SQLITE by default).
    :return:
    """
    SQLSession.configure(bind=database.engine)
    session = SQLSession()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


class DictMixin:
    def as_dict(self) -> dict:
        """
        Return self as a {column: value} dictionary.
        :return:
        """
        return {
            key: value
            for key, value in self.__dict__.items()
            if not key.startswith('_')
        }

    def copy(self):
        return type(self)(**self.as_dict())

    def __str__(self):
        arg_str = ', '.join(
            [f'{key} = {value}' for key, value in self.as_dict().items()]
        )
        return f'{type(self).__name__}({arg_str})'


class Patient(Base, DictMixin):
    __tablename__ = 'dim_patient'
    patient_id = Column(
        String,
        CheckConstraint('patient_id != ""'),
        primary_key=True,
        comment='Patient identifier (pseudonym)',
    )
    created_at = Column(
        DateTime, default=utc_datetime, comment='Patient creation date and time'
    )

    @classmethod
    def add_new(cls, patient_id: str, database: Database):
        patient = cls(patient_id=patient_id)
        logger.debug(f'Add patient {patient.patient_id} to database')
        database.insert(patient)


class Session(Base, DictMixin):
    __tablename__ = 'dim_session'
    session_id = Column(
        String,
        primary_key=True,
        default=generate_unique_id,
        comment='Autogenerated session identifier (UUID v1)',
    )
    started_at = Column(DateTime, comment='Software session start UTC+0 datetime')
    sw_version = Column(String, default=__version__)
    # Global instance
    instance = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.started_at is None:
            self.started_at = utc_datetime()


class EventType(Base, DictMixin):
    __tablename__ = 'dim_event_type_lookup'
    event_type = Column(
        String,
        primary_key=True,
        comment='Event type identifier (e.g., "D" for distraction)',
    )
    event_type_description = Column(String)

    @classmethod
    def distraction_event_type(cls):
        """ Return EventType for distraction event. """
        return cls(event_type='D', event_type_description='Distraction event')

    @classmethod
    def event_types(cls) -> List:
        """ Return list of supported event types. """
        return [cls.distraction_event_type()]


class SensorInfo(Base, DictMixin):
    __tablename__ = 'dim_hw_sensor'
    # serial number as natural primary key
    sensor_serial_number = Column(
        String, primary_key=True, comment='Sensor serial number'
    )
    sensor_name = Column(String, comment='Sensor name')
    turns_in_full_turn = Column(
        Numeric, comment='Sensor-specific number of turns in one full turn.'
    )


class DistractorType:
    KLS_ARNAUD = 'KLS Martin Arnaud'
    KLS_RED = 'KLS Martin RED'


class DistractorInfo(Base, DictMixin):
    __tablename__ = 'dim_hw_distractor_lookup'
    distractor_type = Column(String, primary_key=True)
    displacement_mm_per_full_turn = Column(
        Numeric,
        nullable=False,
        comment='Distractor-specific displacement (mm) per full turn. '
        'The value is determined during hardware calibration.',
    )

    @classmethod
    def distractor_infos(cls):
        return [
            cls(
                distractor_type=DistractorType.KLS_ARNAUD,
                displacement_mm_per_full_turn=1.0,
            ),
            cls(
                distractor_type=DistractorType.KLS_RED,
                displacement_mm_per_full_turn=0.5,
            ),
        ]


class Document(Base, DictMixin):
    __tablename__ = 'dim_document'
    document_id = Column(
        String,
        primary_key=True,
        default=generate_unique_id,
        comment='Autogenerated document identifier (UUID v1)',
    )
    session_id = Column(String, ForeignKey(Session.session_id), nullable=False)
    patient_id = Column(String, ForeignKey(Patient.patient_id), nullable=False)
    sensor_serial_number = Column(
        String,
        ForeignKey(SensorInfo.sensor_serial_number),
        nullable=False,
        comment='Sensor serial number (e.g., FTSLQ6QIA)',
    )
    distractor_number = Column(Integer, comment='Distractor number')
    distractor_type = Column(
        String, ForeignKey(DistractorInfo.distractor_type), nullable=False
    )
    started_at = Column(DateTime, comment='Data collection start date and time (UTC+0)')
    operator = Column(String, comment='Person responsible for the distraction')
    notes = Column(String, comment='User notes')
    full_turn_count = Column(
        Numeric, comment='Number of performed full turns (decimals supported)'
    )

    def get_related_time_series(
        self, database: Database
    ) -> Tuple[List[float], List[float]]:
        """
        Return torque as a function of time related to the document.

        :param database:
        :return:
        """
        x, y = list(), list()
        with session_scope(database) as s:
            measurements = (
                s.query(Measurement)
                .filter(Measurement.document_id == self.document_id)
                .all()
            )
            if len(measurements) == 0:
                return x, y
            x, y = zip(*[(float(m.time_s), float(m.torque_Nm)) for m in measurements])
        return x, y

    def get_related_events(self, database: Database) -> List['AnnotatedEvent']:
        """
        Return list of annotated events related to the document.

        :return:
        """
        with session_scope(database) as s:
            events = (
                s.query(AnnotatedEvent)
                .filter(AnnotatedEvent.document_id == self.document_id)
                .all()
            )
        return events

    def get_related_sensor_info(self, database: Database) -> SensorInfo:
        """
        Return SensorInfo object related to the document.

        :return:
        """
        with session_scope(database) as s:
            sensor_info = (
                s.query(SensorInfo)
                .filter(SensorInfo.sensor_serial_number == self.sensor_serial_number)
                .first()
            )
        return sensor_info

    def insert_time_series(
        self, database: Database, time_s: Iterable[float], torque_Nm: Iterable[float]
    ) -> List['Measurement']:
        """
        Insert torque as a function of time to database.

        :param database:
        :param time_s:
        :param torque_Nm:
        :return:
        """
        # Insert entire time series in one transaction
        measurements = [
            Measurement(document_id=self.document_id, time_s=x, torque_Nm=y)
            for x, y in zip(time_s, torque_Nm)
        ]
        database.bulk_insert(measurements)
        return measurements


class AnnotatedEvent(Base, DictMixin):
    __tablename__ = 'fact_annotated_event'
    event_type = Column(
        String,
        ForeignKey(EventType.event_type),
        primary_key=True,
        comment='Event type identifier',
    )
    event_num = Column(Integer, primary_key=True, comment='Event number')
    document_id = Column(String, ForeignKey(Document.document_id), primary_key=True)
    event_begin = Column(Numeric, comment='Allow placeholder as NULL')
    event_end = Column(Numeric, comment='Allow placeholder as NULL')
    annotation_done = Column(
        Boolean,
        comment='Indicates whether the annotation has been done or if the event is '
        'just a placeholder to be annotated later',
        nullable=False,
    )
    recorded = Column(
        Boolean,
        comment='Indicates if the event was recorded. '
        'If false, the event did occur but the operator failed to record it.',
        nullable=False,
    )


class Measurement(Base, DictMixin):
    __tablename__ = 'fact_measurement'
    measurement_id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(String, ForeignKey(Document.document_id), nullable=False)
    time_s = Column(
        Numeric,
        nullable=False,
        comment='Time since start of data collection in seconds',
    )
    torque_Nm = Column(
        Numeric, nullable=False, comment='Torque measured from the torque sensor'
    )
