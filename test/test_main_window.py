import pytest
import time
import multiprocessing as mp
from PyQt5.QtCore import QTimer
from daqstore.store import DataStore
from cranio.database import Patient
from cranio.app.window import MainWindow

def test_click_ok_triggers_event_detection_sequence(database_patient_fixture):
    DataStore.queue_cls = mp.Queue
    window = MainWindow()
    # pre-conditions:
    # 1. create, select and lock patient
    window.set_patient(Patient.get_instance().patient_id, lock=True)
    # 2. connect dummy torque sensor
    window.connect_dummy_sensor_action.trigger()
    # 3. measure dummy data (Start -> wait -> Stop)
    window.start_measurement()
    time.sleep(1)
    window.stop_measurement()
    # set timer to stop event detection sequence and click ok
    msec = 500
    QTimer.singleShot(msec, window.measurement_widget.region_plot_window.close)
    window.click_ok()
    # kill producer
    window.producer_process.join()
