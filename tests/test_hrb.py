from twisted.trial.unittest import TestCase
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks
from twisted.web.server import Site

from hrb.bouncer import BounceResource
from hrb.utils import http


class HrbTestCase(TestCase):

    timeout = 1

    def setUp(self):
        self.site_factory = Site(BounceResource([self.add_header]))
        self.port = reactor.listenTCP(0, self.site_factory)
        addr = self.port.getHost()
        self.url = "http://%s:%s/" % (addr.host, addr.port)

    def add_header(self, request):
        request.setHeader('X-UA-Type', 'small')
        return ''

    def tearDown(self):
        self.port.loseConnection()

    @inlineCallbacks
    def test_response(self):
        response = yield http.request(self.url)
        self.assertEqual(response.delivered_body, '')
        self.assertEqual(response.headers.getRawHeaders('X-UA-Type'),
                            ['small'])
