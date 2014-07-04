import hashlib
import json

from twisted.internet.defer import (inlineCallbacks, returnValue, succeed,
                                    Deferred)
from twisted.internet import reactor
from twisted.protocols.memcache import DEFAULT_PORT
from twisted.web.template import flattenString

from pywurfl.algorithms import TwoStepAnalysis

from devproxy.handlers.base import BaseHandler
from devproxy.handlers.wurfl_handler import wurfl_devices
from devproxy.handlers.wurfl_handler import debug
from devproxy.utils.memcached import ReconnectingMemCacheClientFactory


class WurflHandlerException(Exception):
    pass


class WurflHandler(BaseHandler):
    def validate_config(self, config):
        self.header_name = config.get('header_name', 'X-UA-map')
        self.cache_prefix = config.get('cache_prefix', '')
        self.cache_prefix_delimiter = config.get('cache_prefix_delimiter', '#')
        self.cache_lifetime = int(config.get('cache_lifetime', 0))
        self.memcached_config = config.get('memcached', {})
        self.default_ua_map = config.get('default_ua_map', 'web')

    @inlineCallbacks
    def setup_handler(self):
        self.devices = wurfl_devices.devices
        self.algorithm = TwoStepAnalysis(self.devices)
        yield self.connect_to_memcached(**self.memcached_config)
        self.namespace = yield self.get_namespace()
        returnValue(self)

    def connect_to_memcached(self, host="localhost", port=DEFAULT_PORT):
        self.memcached_factory = ReconnectingMemCacheClientFactory()
        reactor.connectTCP(host, port, self.memcached_factory)

        d = Deferred()

        def cb():
            if hasattr(self.memcached_factory, 'client'):
                d.callback(self.memcached_factory.client)
            else:
                reactor.callLater(0, cb)

        cb()

        return d

    @property
    def memcached(self):
        return self.memcached_factory.client

    def get_namespace_key(self):
        return '%s_namespace' % (self.cache_prefix,)

    @inlineCallbacks
    def get_namespace_version(self):
        namespace_key = self.get_namespace_key()
        _, version = yield self.memcached.get(namespace_key)
        if version is None:
            version = 0
            yield self.memcached.set(namespace_key, str(version))
        returnValue(str(version))

    @inlineCallbacks
    def get_namespace(self):
        version = yield self.get_namespace_version()
        returnValue(''.join([
            self.cache_prefix,
            self.cache_prefix_delimiter,
            version,
        ]))

    @inlineCallbacks
    def increment_namespace(self, value=1):
        namespace_key = self.get_namespace_key()
        yield self.memcached.increment(namespace_key, value)
        self.namespace = self.get_namespace()

    @inlineCallbacks
    def get_headers(self, request):
        user_agent = unicode(request.getHeader('User-Agent') or '')
        cache_key = self.get_cache_key(user_agent)
        flags, cached = yield self.memcached.get(cache_key)
        if cached:
            headers = self.handle_request_from_cache(cached, request)
        else:
            headers = yield self.handle_request_and_cache(cache_key,
                user_agent, request)
        returnValue(headers)

    def get_cookies(self, request):
        return succeed([])

    @inlineCallbacks
    def handle_request_and_cache(self, cache_key, user_agent, request):
        headers = self.handle_user_agent(user_agent)
        if headers is None:
            device = self.devices.select_ua(user_agent, search=self.algorithm)
            headers = self.handle_device(request, device)
        yield self.memcached.set(cache_key, json.dumps(headers),
            expireTime=self.cache_lifetime)
        returnValue(headers)

    def handle_request_from_cache(self, cached, request):
        return json.loads(cached)

    def get_cache_key(self, key):
        return ''.join([
            self.namespace,
            self.cache_prefix_delimiter,
            hashlib.md5(key).hexdigest()
        ])

    def get_debug_info(self, request):
        user_agent = unicode(request.getHeader('User-Agent') or '')
        device = self.devices.select_ua(user_agent, search=self.algorithm)
        return flattenString(None, debug.DebugElement(device))

    def handle_user_agent(self, user_agent):
        """User agents unknown to Wurfl may require special handling. Override
        this method to provide it. Return None to indicate no special
        handling."""
        return None

    def handle_device(self, request, device):
        raise NotImplementedError("Subclasses should implement this")
