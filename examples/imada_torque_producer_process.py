import time
import pandas as pd
from craniodistractor.producer import ProducerProcess, all_from_queue
from craniodistractor.imada import ImadaSensor

if __name__ == '__main__':
    p = ProducerProcess('Imada torque producer')
    s = ImadaSensor()
    p.producer.add_sensor(s)
    p.start()
    p.start_event.set()
    # record for 2 seconds
    time.sleep(2)
    p.start_event.clear()
    # NOTE: data_queue must be emptied before joining the thread
    data = pd.concat(all_from_queue(p.data_queue))
    print(data)
    p.join(0.5)
    assert not p.is_alive()