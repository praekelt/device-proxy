from twisted.internet import protocol
from twisted.protocols.memcache import MemCacheProtocol


class ReconnectingMemCacheClientFactory(protocol.ReconnectingClientFactory):

    protocol = MemCacheProtocol

    def buildProtocol(self, addr):
        self.client = self.protocol()
        self.addr = addr
        self.client.factory = self
        self.resetDelay()
        return self.client
