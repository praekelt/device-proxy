from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet import protocol, reactor
from twisted.protocols.memcache import MemCacheProtocol, DEFAULT_PORT

from pywurfl.algorithms import TwoStepAnalysis

from hrb.handlers.base import BaseHandler
from hrb.handlers import wurfl_devices


class WurflHandler(BaseHandler):
    def validate_config(self, config):
        self.cookie_name = config.get('cookie_name', 'X-UA-map')
        self.memcached_config = config.get('memcached', {})

    @inlineCallbacks
    def setup_handler(self):
        self.devices = wurfl_devices.devices
        self.algorithm = TwoStepAnalysis(self.devices)
        self.memcached = yield self.connect_to_memcached(
                **self.memcached_config)

    @inlineCallbacks
    def connect_to_memcached(self, host="localhost", port=DEFAULT_PORT):
        creator = protocol.ClientCreator(reactor, MemCacheProtocol)
        client = yield creator.connectTCP(host, port)
        returnValue(client)

    @inlineCallbacks
    def handle_request(self, request):
        user_agent = unicode(request.getHeader('User-Agent') or '')
        device = yield self.memcached.get(user_agent)
        if not device:
            device = self.devices.select_ua(user_agent, search=self.algorithm)
            yield self.memcached.set(user_agent, device)
        returnValue(self.handle_device(request, device))

    def handle_device(self, request, device):
        if device.resolution_width < 240:
            request.addCookie(self.cookie_name, 'medium')
        else:
            request.addCookie(self.cookie_name, 'high')
