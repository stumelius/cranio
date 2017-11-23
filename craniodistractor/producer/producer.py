''' This module implements the PushProducer base class '''
from sys import stdout
from random import randrange

from zope.interface import implementer
from twisted.python.log import startLogging
from twisted.internet import interfaces, reactor
from twisted.internet.protocol import Factory
from twisted.protocols.basic import LineReceiver

@implementer(interfaces.IPushProducer)
class Producer:
    ''' Base producer class '''

    def __init__(self, proto, count):
        self._proto = proto
        self._goal = count
        self._produced = 0
        self._paused = False

    def pauseProducing(self):
        '''
        When we've produced data too fast, pauseProducing() will be called
        (reentrantly from within resumeProducing's sendLine() method, most
        likely), so set a flag that causes production to pause temporarily.
        '''
        self._paused = True
        print('Pausing connection from %s' % self._proto.transport.getPeer())

    def resumeProducing(self):
        '''
        Resume producing integers.
        This tells the push producer to (re-)add itself to the main loop and
        produce integers for its consumer until the requested number of integers
        were returned to the client.
        '''
        self._paused = False

        while not self._paused and self._produced < self._goal:
            next_int = randrange(0, 10000)
            self._proto.sendLine('%d' % next_int)
            self._produced += 1

        if self._produced == self._goal:
            self._proto.transport.unregisterProducer()
            self._proto.transport.loseConnection()

    def stopProducing(self):
        '''
        When a consumer has died, stop producing data for good.
        '''
        self._produced = self._goal

@implementer(interfaces.IConsumer) 
class Consumer:
    ''' Base consumer class '''
    
    def __init__(self):
        self.cache = []
    
    def registerProducer(self, producer, streaming):
        '''
        Args:
            - producer: producer object
            - streaming: True if producer provides IPushProducer, False if producer provides IPullProducer. (type: bool)
            
        Returns:
            None
            
        Raises:
            RuntimeError    If a producer is already registered.
        '''
        return super(Consumer, self).registerProducer(streaming)
    
    def unregisterProducer(self):
        return super(Consumer, self).unregisterProducer()
    
    def write(self, data):
        ''' The producer writes data by calling this method '''
        # if enough data, call producer.pauseProducing()
        
        # push data to cache
        self.cache.append(data)


class ServeRandom(LineReceiver):
    """
    Serve up random integers.
    """
    
    def __init__(self):
        # FIXME: is this the right place to initialize the transport?
        self.transport = Consumer()

    def connectionMade(self):
        """
        Once the connection is made we ask the client how many random integers
        the producer should return.
        """
        print('Connection made from %s' % self.transport.getPeer())
        self.sendLine('How many random integers do you want?')

    def lineReceived(self, line):
        """
        This checks how many random integers the client expects in return and
        tells the producer to start generating the data.
        """
        count = int(line.strip())
        print('Client requested %d random integers!' % count)
        producer = Producer(self, count)
        self.transport.registerProducer(producer, True)
        producer.resumeProducing()

    def connectionLost(self, reason):
        print('Connection lost from %s' % self.transport.getPeer())


startLogging(stdout)
factory = Factory()
factory.protocol = ServeRandom
reactor.listenTCP(1234, factory)
reactor.run()

# what next? 
# how to connect a producer to server/consumer
    