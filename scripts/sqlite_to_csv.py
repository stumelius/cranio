import pandas as pd

from pathlib import Path
from sqlalchemy import create_engine, Table, MetaData
from sqlalchemy.orm import sessionmaker

SQLSession = sessionmaker()
engine = create_engine('sqlite:///data/craniodistractor.db', echo=False)
SQLSession.configure(bind=engine)

# reflect database objects
meta = MetaData()
meta.reflect(bind=engine)
Data = Table('data', meta, autoload=True)
Session = Table('session', meta, autoload=True)
Patient = Table('patient', meta, autoload=True)

if __name__ == '__main__':
    for Table in (Data, Session, Patient):
        df = pd.read_sql_table(Table.name, engine)
        df.to_csv(Path('data') / 'craniodistractor_{}.csv'.format(Table.name), sep=';', index=False)
    