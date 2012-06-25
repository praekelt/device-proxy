from twisted.trial.unittest import TestCase
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks
from twisted.web.server import Site

from hrb.bouncer import BounceResource
from hrb.utils import http


class HrbTestCase(TestCase):

    def setUp(self):
        self.site_factory = Site(BounceResource({}))
        self.port = reactor.listenTCP(0, self.site_factory)
        addr = self.port.getHost()
        self.url = "http://%s:%s/" % (addr.host, addr.port)

    def tearDown(self):
        self.port.loseConnection()

    @inlineCallbacks
    def test_response(self):
        response = yield http.request(self.url)
        self.assertEqual(response.delivered_body, 'hello')
