import os
import subprocess
import signal
from contextlib import contextmanager
from craniodistractor.core.protocol import Connection
from craniodistractor.core.packet import Packet
from craniodistractor.server.echo_server import run_server

@contextmanager
def run_server():
    print('Starting server ...')
    p = subprocess.Popen('python -c "from craniodistractor.server.echo_server import run_server; run_server()"', stdout=subprocess.PIPE, shell=True)
    print('... success!')
    yield p
    #print('Killing server ...')
    #os.kill(p.pid, signal.SIGTERM)
    #print('... success!')
    
with run_server() as p:
    conn = Connection('localhost', 50300)
    with conn.open():
        for i in range(10):
            p_send = Packet.random()
            conn.send(p_send)
            p_recv = Packet.decode(conn.recv())
            print(i, 'Received: ' + str(p_recv))
            assert p_send == p_recv