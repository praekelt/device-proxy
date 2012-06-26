from twisted.trial.unittest import TestCase
from twisted.protocols.memcache import DEFAULT_PORT
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.web.server import Site

from hrb.bouncer import BounceResource
from hrb.handlers.base import BaseHandler
from hrb.handlers.wurfl import WurflHandler
from hrb.utils import http


class TestHandler(BaseHandler):
    def __init__(self, callback):
        self.callback = callback

    def setup_handler(self):
        pass

    def teardown_handler(self):
        pass

    def handle_request(self, request):
        return self.callback(request)


class FakeMemcached(object):
    def __init__(self):
        self._data = {}
        self._calls = {}

    def set(self, key, value):
        self._data[key] = value

    def get(self, key):
        if key in self._data:
            call_counter = self._calls.setdefault(key, 0)
            call_counter += 1
            self._calls[key] = call_counter
            return self._data.get(key)

    def __contains__(self, key):
        return key in self._data

    def times_called(self, key):
        return self._calls.get(key)


class HrbTestCase(TestCase):

    timeout = 1

    def setUp(self):
        self._running_handlers = []
        self.header_handlers = map(TestHandler, [
            lambda request: request.setHeader('X-UA-Type', 'small'),
            lambda request: request.setHeader('X-UA-Category', 'mobi'),
        ])

        self.body_handlers = map(TestHandler, [
            lambda request: 'foo',
            lambda request: 'bar',
        ])

        self.cookie_handlers = map(TestHandler, [
            lambda request: request.addCookie('UA-Foo', 'bar')
        ])

        self.fake_memcached = FakeMemcached()
        self.patch(WurflHandler, 'connect_to_memcached', self.patch_memcached)

        self.nokia_ua = 'Nokia3100/1.0 (02.70) Profile/MIDP-1.0 ' \
                            'Configuration/CLDC-1.0'

        self.iphone_ua = 'Mozilla/5.0 (iPhone; U; CPU iPhone OS 2_2_1 ' \
                            'like Mac OS X; en-us) AppleWebKit/525.18.1 ' \
                            '(KHTML, like Gecko) Version/3.1.1 Mobile/5H11 ' \
                            'Safari/525.20'

    def patch_memcached(self, **config):
        return self.fake_memcached

    def get_wurfl_handler(self):
        return WurflHandler({
            'cookie_name': 'X-UA-header',
        })

    @inlineCallbacks
    def start_handlers(self, handlers):
        for handler in handlers:
            yield handler.setup_handler()

        site_factory = Site(BounceResource(handlers))
        port = reactor.listenTCP(0, site_factory)
        addr = port.getHost()
        url = "http://%s:%s/" % (addr.host, addr.port)
        self._running_handlers.append((port, handlers))
        returnValue(url)

    @inlineCallbacks
    def tearDown(self):
        for port, handlers in self._running_handlers:
            for handler in handlers:
                yield handler.teardown_handler()
            port.loseConnection()

    @inlineCallbacks
    def test_response_headers(self):
        url = yield self.start_handlers(self.header_handlers)
        response = yield http.request(url)
        self.assertEqual(response.delivered_body, '')
        self.assertEqual(response.headers.getRawHeaders('X-UA-Type'),
                            ['small'])
        self.assertEqual(response.headers.getRawHeaders('X-UA-Category'),
                            ['mobi'])

    @inlineCallbacks
    def test_response_body(self):
        url = yield self.start_handlers(self.body_handlers)
        response = yield http.request(url)
        self.assertEqual(response.delivered_body, 'foobar')

    @inlineCallbacks
    def test_response_cookies(self):
        url = yield self.start_handlers(self.cookie_handlers)
        response = yield http.request(url)
        self.assertEqual(response.headers.getRawHeaders('Set-Cookie'),
            ['UA-Foo=bar'])

    @inlineCallbacks
    def test_wurfl_nokia_lookup(self):
        wurfl_handler = self.get_wurfl_handler()
        url = yield self.start_handlers([wurfl_handler])
        response = yield http.request(url, headers={
            'User-Agent': self.nokia_ua,
            })
        self.assertEqual(response.headers.getRawHeaders('Set-Cookie'),
                ['%s=medium' % wurfl_handler.cookie_name])

    @inlineCallbacks
    def test_wurfl_iphone_lookup(self):
        wurfl_handler = self.get_wurfl_handler()
        url = yield self.start_handlers([wurfl_handler])
        response = yield http.request(url, headers={
            'User-Agent': self.iphone_ua,
            })
        self.assertEqual(response.headers.getRawHeaders('Set-Cookie'),
                ['%s=high' % wurfl_handler.cookie_name])

    @inlineCallbacks
    def test_caching_wurl_check(self):
        wurfl_handler = self.get_wurfl_handler()
        url = yield self.start_handlers([wurfl_handler])
        yield http.request(url, headers={
            'User-Agent': self.iphone_ua,
            })
        cache_key = wurfl_handler.get_cache_key(self.iphone_ua)
        self.assertTrue(cache_key in self.fake_memcached)

        response = yield http.request(url, headers={
            'User-Agent': self.iphone_ua,
            })

        self.assertEqual(self.fake_memcached.times_called(cache_key), 1)
        self.assertTrue(self.fake_memcached.get(cache_key))
        self.assertEqual(response.headers.getRawHeaders('Set-Cookie'),
            ['%s=high' % wurfl_handler.cookie_name])

    @inlineCallbacks
    def test_redirect_after_cookie_is_set(self):
        wurfl_handler = self.get_wurfl_handler()
        url = yield self.start_handlers([wurfl_handler])
        request_path = "some/random/path?true=1"
        response = yield http.request('%s%s' % (url, request_path),
            headers={
                'User-Agent': self.iphone_ua,
            })
        self.assertEqual(response.code, 302)
        self.assertEqual(response.headers.getRawHeaders('Location'),
            ['/%s' % (request_path,)])
