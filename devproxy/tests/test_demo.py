from twisted.internet.defer import inlineCallbacks

from devproxy.tests.utils import ProxyTestCase
from devproxy.utils import http
from devproxy.handlers.demo import DemoHandler


class DemoHandlerTestCase(ProxyTestCase):

    @inlineCallbacks
    def setUp(self):
        yield super(DemoHandlerTestCase, self).setUp()
        self.demo_handlers = yield self.start_handlers([DemoHandler({
            'cookies': {
                'type': 'dog-biscuit'
            }
        })])

    @inlineCallbacks
    def test_headers(self):
        proxy, url = self.start_proxy(self.demo_handlers)
        response = yield http.request(url)
        self.assertEqual(response.delivered_body, 'foo')
        req = yield self.mocked_backend.queue.get()
        self.assertEqual(
            req.requestHeaders.getRawHeaders('x-device-is-dumb'),
            ['Very'])

    @inlineCallbacks
    def test_cookies(self):
        proxy, url = self.start_proxy(self.demo_handlers)
        resp = yield http.request(url, method='GET')
        self.assertEqual(resp.delivered_body, 'foo')
        req = yield self.mocked_backend.queue.get()
        self.assertFalse(req.requestHeaders.hasHeader('Set-Cookie'))
        self.assertTrue(resp.headers.hasHeader('Set-Cookie'))
        self.assertEqual(resp.headers.getRawHeaders('Set-Cookie'), [
            'type=dog-biscuit'])
