import time
from craniodistractor.core import Packet
from craniodistractor.producer import ProducerProcess
from craniodistractor.imada import ImadaSensor

if __name__ == '__main__':
    p = ProducerProcess('Imada torque producer')
    s = ImadaSensor()
    p.producer.add_sensor(s)
    p.start()
    # record for 2 seconds
    time.sleep(2)
    p.pause()
    # NOTE: data_queue must be emptied before joining the thread
    data = Packet.concat(p.get_all())
    print(data.as_dataframe())
    p.join()
    assert not p.is_alive()