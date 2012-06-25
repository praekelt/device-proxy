from twisted.trial.unittest import TestCase
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks
from twisted.web.server import Site

from hrb.bouncer import BounceResource
from hrb.utils import http


class HrbTestCase(TestCase):

    timeout = 1

    def setUp(self):
        self.default_handlers = [
            lambda request: request.setHeader('X-UA-Type', 'small'),
            lambda request: request.setHeader('X-UA-Category', 'mobi'),
        ]
        self._running_handlers = []

    def start_handlers(self, handlers):
        site_factory = Site(BounceResource(handlers))
        port = reactor.listenTCP(0, site_factory)
        addr = port.getHost()
        url = "http://%s:%s/" % (addr.host, addr.port)
        self._running_handlers.append(port)
        return url

    def tearDown(self):
        for port in self._running_handlers:
            port.loseConnection()

    @inlineCallbacks
    def test_response_headers(self):
        url = self.start_handlers(self.default_handlers)
        response = yield http.request(url)
        self.assertEqual(response.delivered_body, '')
        self.assertEqual(response.headers.getRawHeaders('X-UA-Type'),
                            ['small'])
        self.assertEqual(response.headers.getRawHeaders('X-UA-Category'),
                            ['mobi'])

    @inlineCallbacks
    def test_response_body(self):

        def handler_1(request):
            request.setHeader('X-Foo', 'bar')
            return 'foo'

        def handler_2(request):
            request.setHeader('X-Bar', 'foo')
            return 'bar'

        url = self.start_handlers([handler_1, handler_2])
        response = yield http.request(url)
        self.assertEqual(response.delivered_body, 'foobar')
        self.assertEqual(response.headers.getRawHeaders('X-Foo'), ['bar'])
        self.assertEqual(response.headers.getRawHeaders('X-Bar'), ['foo'])
