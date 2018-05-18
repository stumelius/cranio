import enum
from contextlib import contextmanager
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Enum, ForeignKey, create_engine
from cranio.core import generate_unique_id

# define database connection
# TODO: replace in-memory database
#engine = create_engine(f'sqlite:///{DATABASE_NAME}.db')
engine = create_engine('sqlite://')
Base = declarative_base()
SQLSession = sessionmaker(bind=engine)


@contextmanager
def session_scope():
    ''' Provide a transactional scope around a series of operations. '''
    session = SQLSession()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


class Patient(Base):
    __tablename__ = 'dim_patient'
    id = Column(String, primary_key=True)


class Session(Base):
    __tablename__ = 'dim_session'
    id = Column(String, primary_key=True, default=generate_unique_id)
    patient_id = Column(String, ForeignKey('dim_patient.id'), nullable=False)
    datetime = Column(DateTime)


class Document(Base):
    __tablename__ = 'dim_document'
    id = Column(String, primary_key=True, default=generate_unique_id)
    session_id = Column(String, ForeignKey('dim_session.id'), nullable=False)
    distractor_id = Column(Integer)
    datetime = Column(DateTime)
    document_type = Column(String)
    schema_version = Column(String)
    operator = Column(String)
    notes = Column(String)
    distraction_achieved = Column(Float)
    # comma-separated list
    missed_distractors = Column(String)
    distraction_plan_followed = Column(Boolean)


class Measurement(Base):
    __tablename__ = 'fact_measurement'
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(String, ForeignKey('dim_document.id'), nullable=False)
    time_s = Column(Float, nullable=False)
    torque_Nm = Column(Float, nullable=False)


class LogLevel(enum.Enum):
    DEBUG = 0
    INFO = 1
    ERROR = 2


class Log(Base):
    ''' Software log table '''
    __tablename__ = 'fact_log'
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(String, ForeignKey('dim_document.id'), nullable=False)
    datetime = Column(DateTime, nullable=False)
    level = Column(Enum(LogLevel), nullable=False)
    message = Column(String, nullable=False)


# create database schema
Base.metadata.create_all(engine)
