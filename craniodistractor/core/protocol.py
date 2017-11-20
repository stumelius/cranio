import socket
from contextlib import contextmanager
from craniodistractor.core.packet import Packet

class Connection:
    
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    @contextmanager
    def open(self):
        yield self.socket.connect((self.host, self.port))
        self.socket.close()
        
    def send(self, packet):
        self.socket.send(packet.encode())
        
    def recv(self, buffersize=1024):
        return self.socket.recv(buffersize)
    
    def self_test(self):
        with self.open():
            p = Packet.random()
            self.send(p)

def open_connection():
    pass

def close_connection():
    pass