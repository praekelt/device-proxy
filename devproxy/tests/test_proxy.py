from twisted.internet import defer
from twisted.internet.defer import inlineCallbacks

from devproxy.utils import http
from devproxy.tests.utils import (HeaderHandler, CookieHandler, DebugHandler,
                                    ProxyTestCase)
from devproxy.handlers.base import Cookie


class ProxyTestCase(ProxyTestCase):

    @inlineCallbacks
    def setUp(self):
        yield super(ProxyTestCase, self).setUp()
        self.header_handlers = yield self.start_handlers(map(HeaderHandler, [
            lambda request: defer.succeed([{'X-UA-Type': 'small'}]),
            lambda request: defer.succeed([{'X-UA-Category': 'mobi'}]),
            ]))

        self.cookie_handlers = yield self.start_handlers(map(CookieHandler, [
            lambda request: defer.succeed([Cookie('Type', 'Chocolate Chip')]),
            lambda request: defer.succeed([Cookie('Delicious', 'Definitely')]),
            ]))

        self.debug_handlers = yield self.start_handlers(map(DebugHandler, [
            lambda request: defer.succeed('debugfoo'),
            lambda request: defer.succeed('debugbar'),
            ]))

    @inlineCallbacks
    def test_setting_header(self):
        proxy, url = self.start_proxy(self.header_handlers)
        resp = yield http.request(url, method='GET')
        self.assertEqual(resp.delivered_body, 'foo')
        req = yield self.mocked_backend.queue.get()
        self.assertEqual(req.requestHeaders.getRawHeaders('x-ua-type'),
            ['small'])
        self.assertEqual(req.requestHeaders.getRawHeaders('x-ua-category'),
            ['mobi'])

    @inlineCallbacks
    def test_setting_cookie(self):
        proxy, url = self.start_proxy(self.cookie_handlers)
        resp = yield http.request(url, method='GET')
        self.assertEqual(resp.delivered_body, 'foo')
        req = yield self.mocked_backend.queue.get()
        self.assertFalse(req.requestHeaders.hasHeader('Set-Cookie'))
        self.assertTrue(resp.headers.hasHeader('Set-Cookie'))
        self.assertEqual(resp.headers.getRawHeaders('Set-Cookie'), [
            'Type=Chocolate Chip', 'Delicious=Definitely'])

    @inlineCallbacks
    def test_debug_info(self):
        proxy, url = self.start_proxy(self.debug_handlers)
        resp = yield http.request('%s/_debug' % (url,), method='GET')
        self.assertTrue('debugfoo' in resp.delivered_body)
        self.assertTrue('debugbar' in resp.delivered_body)
