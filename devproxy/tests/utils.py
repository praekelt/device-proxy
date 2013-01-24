from devproxy.handlers.base import BaseHandler
from devproxy.proxy import ReverseProxyResource

from twisted.trial.unittest import TestCase
from twisted.internet import defer, reactor
from twisted.web.resource import Resource
from twisted.web.server import Site


class ProxyTestCase(TestCase):

    timeout = 1

    nokia_ua = 'Nokia3100/1.0 (02.70) Profile/MIDP-1.0 ' \
                'Configuration/CLDC-1.0'

    iphone_ua = 'Mozilla/5.0 (iPhone; U; CPU iPhone OS 2_2_1 ' \
                'like Mac OS X; en-us) AppleWebKit/525.18.1 ' \
                '(KHTML, like Gecko) Version/3.1.1 Mobile/5H11 ' \
                'Safari/525.20'

    def setUp(self):
        self._running_proxies = []
        self.mocked_backend = MockHttpServer(self.handle_request)
        return self.mocked_backend.start()

    @defer.inlineCallbacks
    def start_handlers(self, handlers):
        started_handlers = []
        for handler in handlers:
            started_handlers.append((yield handler.setup_handler()))
        defer.returnValue(started_handlers)

    def tearDown(self):
        for port, proxy_factory in self._running_proxies:
            port.loseConnection()
        self.mocked_backend.stop()

    def handle_request(self, request):
        self.mocked_backend.queue.put(request)
        return 'foo'

    def start_proxy(self, handlers):
        proxy = ReverseProxyResource(handlers, '/_debug', '/_health',
            self.mocked_backend.addr.host, self.mocked_backend.addr.port, '')
        site_factory = Site(proxy)
        port = reactor.listenTCP(0, site_factory)
        addr = port.getHost()
        url = "http://%s:%s" % (addr.host, addr.port)
        self._running_proxies.append((port, proxy))
        return (proxy, url)


class TestHandler(BaseHandler):
    def __init__(self, header_callback=None, cookie_callback=None,
                    debug_callback=None):
        noop = lambda _: None
        self.header_callback = header_callback or noop
        self.cookie_callback = cookie_callback or noop
        self.debug_callback = debug_callback or noop

    def setup_handler(self):
        d = defer.Deferred()
        reactor.callLater(0, d.callback, self)
        return d

    def teardown_handler(self):
        pass

    def get_headers(self, request):
        return self.header_callback(request)

    def get_cookies(self, request):
        return self.cookie_callback(request)

    def get_debug_info(self, request):
        return self.debug_callback(request)


class HeaderHandler(TestHandler):
    def __init__(self, callback):
        super(HeaderHandler, self).__init__(header_callback=callback)


class CookieHandler(TestHandler):
    def __init__(self, callback):
        super(CookieHandler, self).__init__(cookie_callback=callback)


class DebugHandler(TestHandler):
    def __init__(self, callback):
        super(DebugHandler, self).__init__(debug_callback=callback)


class FakeMemcached(object):
    def __init__(self):
        self._data = {}
        self._calls = {}

    def set(self, key, value, expireTime=0):
        self._data[key] = (value, expireTime)

    def get(self, key):
        if key in self._data:
            call_counter = self._calls.setdefault(key, 0)
            call_counter += 1
            self._calls[key] = call_counter
            value, _ = self._data.get(key)
            return 0, value
        return 0, None

    def increment(self, key, value):
        int_val = int(self._data[key][0])
        int_val += int(value)
        self.set(key, str(int_val))
        return str(int_val)

    def __contains__(self, key):
        return key in self._data

    def times_called(self, key):
        return self._calls.get(key)

    def key_lifetime(self, key):
        value, life_time = self._data.get(key)
        return life_time


class MockResource(Resource):
    isLeaf = True

    def __init__(self, handler):
        Resource.__init__(self)
        self.handler = handler

    def render_GET(self, request):
        return self.handler(request)

    def render_POST(self, request):
        return self.handler(request)


class MockHttpServer(object):

    def __init__(self, handler=None):
        self.queue = defer.DeferredQueue()
        self._handler = handler or self.handle_request
        self._webserver = None
        self.addr = None
        self.url = None

    def handle_request(self, request):
        self.queue.put(request)

    @defer.inlineCallbacks
    def start(self):
        root = MockResource(self._handler)
        site_factory = Site(root)
        self._webserver = yield reactor.listenTCP(0, site_factory)
        self.addr = self._webserver.getHost()
        self.url = "http://%s:%s/" % (self.addr.host, self.addr.port)

    @defer.inlineCallbacks
    def stop(self):
        yield self._webserver.loseConnection()
