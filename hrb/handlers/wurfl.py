from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.protocols.memcache import MemCacheProtocol, DEFAULT_PORT

from pywurfl.algorithms import TwoStepAnalysis
from hrb.handlers import wurfl_devices

class WurflHandler(object):
    def __init__(self, config):
        self.config = config
        self.devices = wurfl_devices.devices
        self.algorithm = TwoStepAnalysis(self.devices)
    
    @inlineCallbacks
    def setup_handler(self):
        self.memcached = yield self.connect_to_memcached(
                **self.options.get('memcached', {}))

    @inlineCallbacks
    def connect_to_memcached(self, host="localhost", port=DEFAULT_PORT):
        creator = protocol.ClientCreator(reactor, MemCacheProtocol)
        client = yield creator.connectTCP(host, port)
        returnValue(client)

    def teardown_handler(self):
        pass

    def handle_request(self, request):
        user_agent = unicode(request.getHeader('User-Agent') or '')
        device = self.devices.select_ua(user_agent, search=self.algorithm)
        return self.handle_device(request, device)
    
    def handle_device(self, request, device):
        if device.resolution_width < 240:
            request.addCookie('X-UA-map', 'medium')
        else:
            request.addCookie('X-UA-map', 'high')
        return ''

