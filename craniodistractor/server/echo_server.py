import socket
from craniodistractor.core.packet import Packet

def run_server(host='', port=50300):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((host, port))
    print(host, port)
    s.listen(1)
    conn, addr = s.accept()
    print('Connected by', addr)
    while True:
        try:
            bytes = conn.recv(1024)
            p = Packet.decode(bytes)
            if not p: break
            print('Client Says: ' + repr(p))
            conn.sendall(bytes)
        except socket.error as e:
            print(str(e))
            break
    
    conn.close()

if __name__ == '__main__':
    run_server()