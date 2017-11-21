''' Simple echo server based on the Twisted web framework. '''
from twisted.internet import reactor, protocol, endpoints
#from craniodistractor.core.packet import Packet

# http://twistedmatrix.com/documents/current/core/howto/producers.html

class Echo(protocol.Protocol):
    ''' Simple echo protocol '''
    def __init__(self, factory):
        self.factory = factory

    def connectionMade(self):
        self.factory.numProtocols = self.factory.numProtocols + 1
        self.transport.write(
            'Welcome! There are currently {} open connections.\n'.\
            format(self.factory.numProtocols).encode())

    def connectionLost(self, reason):
        self.factory.numProtocols -= 1
        
    def dataReceived(self, data):
        self.transport.write(data)
        
class EchoFactory(protocol.Factory):
    ''' Echo protocol factory '''
    
    def __init__(self):
        self.numProtocols = 0
        
    def buildProtocol(self, addr):
        return Echo(self)

def run_server(port=50300):
    ''' 
    Runs the echo server on specified host and port.
    
    Test example: 
    
    >>> telnet open localhost 50300
    Welcome! There are currently 1 open connections.
    
    '''
    endpoint = endpoints.TCP4ServerEndpoint(reactor, port)
    endpoint.listen(EchoFactory())
    reactor.run()

if __name__ == '__main__':
    run_server()
