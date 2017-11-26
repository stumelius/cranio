'''
MODULE DESCRIPTION

Copyright (C) 2017  Simo Tumelius

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
'''

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