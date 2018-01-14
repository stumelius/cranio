# Extract, transform and load old craniodistractor data
# Loading to a database and csv files

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

from contextlib import contextmanager
from pathlib import Path
from cranio.imada import decode_telegram, TelegramError
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLSession = sessionmaker()
Base = declarative_base()
engine = create_engine('sqlite:///craniodistractor.db', echo=False)
SQLSession.configure(bind=engine)

@contextmanager
def sqlsession_scope():
    '''Provide a transactional scope around a series of operations.'''
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
    __tablename__ = 'patient'
    
    patient_id = Column(Integer, primary_key=True)
    patient_alias = Column(String)

class Session(Base):
    __tablename__ = 'session'
    
    session_id = Column(Integer, primary_key=True)
    session_name = Column(String)
    patient_id = Column(Integer, ForeignKey(Patient.patient_id))

class Data(Base):
    __tablename__ = 'data'
    
    id = Column(Integer, primary_key=True)
    time_s = Column(Float)
    torque_Nm = Column(Float)
    force_N = Column(Float)
    event = Column(String)
    session_id = Column(Integer, ForeignKey(Session.session_id))
    
Base.metadata.create_all(engine)

def extract(fpath: str) -> pd.DataFrame:
    # skip the first two rods and read as a csv
    df = pd.read_csv(fpath, skiprows=2, header=None, delim_whitespace=True)
    return df

def transform(df: pd.DataFrame) -> pd.DataFrame:
    # rename columns (torque and time)
    df_out = df.rename({0: 'torque (Nm)', 1: 'time (s)'}, axis=1)
    # decode torque strings to float
    df_out['torque (Nm)'] = df_out['torque (Nm)'].map(lambda x: decode_telegram(x)[0])
    return df_out

def load_to_db(df: pd.DataFrame, sqlsession):
    df_out = df.rename({'torque (Nm)': 'torque_Nm', 'time (s)': 'time_s'}, axis=1)
    data = [Data(**series.to_dict()) for _,series in df_out.iterrows()]
    sqlsession.add_all(data)
    return df_out

# input data folder
fpath_in = Path(r'Z:\Impact & Pocidon\02012013\Impact\Applied research\Craniosynostosis\Craniodistraction\4. Force Measurements\2. Data')

# iterate through each patient folder
folders = [x for x in fpath_in.iterdir() if 'rawPatient' in x.name]
for folder in folders:
    with sqlsession_scope() as sqlsession:
        # folder name as patient_alias
        patient_alias = folder.stem
        patient = Patient(patient_alias=patient_alias)
        sqlsession.add(patient)
        # flush to realize autoincrement patient_id
        sqlsession.flush()
        # iterate over data files
        txt_files = [x for x in folder.iterdir() if x.suffix == '.txt']
        for f in txt_files:
            # path stem/basename as session_name
            session_name = f.stem
            session = Session(session_name=session_name, patient_id=patient.patient_id)
            try:
                # extract and transform data
                df_data = transform(extract(f))
                sqlsession.add(session)
                # flush to realize autoincrement session_id
                sqlsession.flush()
                df_data['session_id'] = session.session_id
                data = load_to_db(df_data, sqlsession)
                print('Patient {} - session {} loaded to database'.format(patient.patient_id, session_name))
            except TelegramError:
                print('Failed to load Patient {} - session {} (TelegramError)'.format(patient.patient_id, session_name))

# query: number of rows in each table
sqlsession = SQLSession()

for Table in (Data, Session, Patient):
    n_rows = sqlsession.query(Table).count()
    print('Number of rows in {}: {}'.format(Table.__tablename__, n_rows))


# write tables to csv files
for Table in (Patient, Session, Data):
    df = pd.read_sql_table(Table.__tablename__, engine)
    df.to_csv('craniodistractor_{}.csv'.format(Table.__tablename__), sep=';', index=False)