import sys

import pandas as pd

from contextlib import contextmanager
from sqlalchemy import create_engine, Table, MetaData
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.automap import automap_base
from cranio.core import Event
from cranio.app.plot import RegionWindow, RegionWidget as RegionWidgetParent

#Base = automap_base()
SQLSession = sessionmaker()
engine = create_engine('sqlite:///data/craniodistractor.db', echo=False)
SQLSession.configure(bind=engine)

# reflect database objects
meta = MetaData()
meta.reflect(bind=engine)
Data = Table('data', meta, autoload=True)
Session = Table('session', meta, autoload=True)
Patient = Table('patient', meta, autoload=True)

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
        
def read_data():
    return map(lambda x: pd.read_sql_table(x.name, engine),
               (Data, Session, Patient))
    
def join_data(data: pd.DataFrame, session: pd.DataFrame, patient: pd.DataFrame):
    df = data.merge(session, how='left', on='session_id')
    return df.merge(patient, how='left', on='patient_id')


class RegionWidget(RegionWidgetParent):
    
    def next_event(self):
        ''' Determines the next event '''
        numbers = set(range(1, len(self.region_edit_map)+1))
        used_numbers = {w.distraction_event.num for w in self.region_edit_map.values() if hasattr(w, 'distraction_event')}
        available_numbers = list(numbers - used_numbers)
        assert len(available_numbers) == 1
        return Event(Event.DISTRACTION, available_numbers[0])
    
    def add_region(self, *args, **kwargs):
        ''' Overload. Adds a region name to the edit widget. '''
        edit_widget = super(RegionWidget, self).add_region(*args, **kwargs)
        edit_widget.name_edit.setEnabled(False)
        edit_widget.distraction_event = self.next_event()
        edit_widget.name = str(edit_widget.distraction_event)
        return edit_widget

def run():
    ''' Graphical annotation '''
    df = join_data(*list(read_data()))
    sessions = df['session_id'].unique()
    session_id = sessions[9]
    df_session = df[df['session_id'] == session_id]

    p = RegionWindow()
    w = RegionWidget()
    p.add_plot(w)
    
    # plot data
    w.plot(df_session['time_s'], df_session['torque_Nm'])
    w.x_label = 'time (s)'
    w.y_label = 'torque (Nm)'
    
    # add regions for existing events
    for key, df_event in df_session.groupby('event'):
        t = df_event['time_s']
        edit_widget = w.add_region((t.min(), t.max()))
        edit_widget.name = key
    
    # run graphical annotation
    ret = p.exec_()
    
    # extract only Data table columns
    df_data = df[[c.name for c in Data.columns]]
    # remove old events from session data
    if len(w.region_edit_map) > 0:
        df_data.loc[df_data['session_id'] == session_id, 'event'] = None
    for edit_widget in w.region_edit_map.values():
        x_range = sorted(edit_widget.region())
        df_data.loc[(df_data['session_id'] == session_id) \
                    & (df_data['time_s'] >= x_range[0]) \
                    & (df_data['time_s'] <= x_range[1]), 'event'] = edit_widget.name
    df_data.to_sql(str(Data), engine, if_exists='replace', index=False)
    return ret

if __name__ == '__main__':
    sys.exit(run())