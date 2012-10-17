import hashlib
import json

from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet import protocol, reactor
from twisted.protocols.memcache import MemCacheProtocol, DEFAULT_PORT
from twisted.web.template import flattenString
from twisted.python import log

from pywurfl.algorithms import TwoStepAnalysis

from hrb.handlers.base import BaseHandler
from hrb.handlers.wurfl_handler import wurfl_devices
from hrb.handlers.wurfl_handler import debug


class WurflHandler(BaseHandler):
    def validate_config(self, config):
        self.header_name = config.get('header_name', 'X-UA-map')
        self.cache_prefix = config.get('cache_prefix', '')
        self.cache_prefix_delimiter = config.get('cache_prefix_delimiter', '#')
        self.cache_lifetime = int(config.get('cache_lifetime', 0))
        self.debug_path = config.get('debug_path', None)
        self.memcached_config = config.get('memcached', {})

    @inlineCallbacks
    def setup_handler(self):
        self.devices = wurfl_devices.devices
        self.algorithm = TwoStepAnalysis(self.devices)
        self.memcached = yield self.connect_to_memcached(
                **self.memcached_config)
        self.namespace = yield self.get_namespace()
        returnValue(self)

    def shutdown(self, failure):
        log.err(failure)
        reactor.stop()

    @inlineCallbacks
    def connect_to_memcached(self, host="localhost", port=DEFAULT_PORT):
        creator = protocol.ClientCreator(reactor, MemCacheProtocol)
        client = yield creator.connectTCP(host, port).addErrback(self.shutdown)
        returnValue(client)

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

    @inlineCallbacks
    def get_body(self, request):
        user_agent = unicode(request.getHeader('User-Agent') or '')
        if request.path == self.debug_path:
            device = self.devices.select_ua(user_agent, search=self.algorithm)
            body = yield self.debug_device(request, device)
            returnValue(body)

    @inlineCallbacks
    def handle_request_and_cache(self, cache_key, user_agent, request):
        device = self.devices.select_ua(user_agent, search=self.algorithm)
        headers = self.handle_device(request, device)
        yield self.memcached.set(cache_key, json.dumps(headers),
            expireTime=self.cache_lifetime)
        returnValue(headers)

    def handle_request_from_cache(self, cached, request):
        # JSON returns everything as unicode which Twisted isn't too happy
        # with, encode to utf8 bytestring instead.
        return json.loads(cached)

    def get_cache_key(self, key):
        return ''.join([
            self.namespace,
            self.cache_prefix_delimiter,
            hashlib.md5(key).hexdigest()
        ])

    def debug_device(self, request, device):
        return flattenString(None, debug.DebugElement(device))

    def handle_device(self, request, device):
        raise NotImplementedError("Subclasses should implement this")
