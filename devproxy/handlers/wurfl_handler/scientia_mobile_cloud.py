import base64
import json
import warnings

from devproxy.handlers.wurfl_handler.base import WurflHandler
from twisted.internet.defer import inlineCallbacks, returnValue, Deferred
from twisted.internet import reactor
from twisted.internet.endpoints import HostnameEndpoint, TCP4ClientEndpoint
from twisted.web.client import ProxyAgent, getPage
from twisted.web.http_headers import Headers
from twisted.internet import protocol


class ScientiaMobileCloudHandlerConnectError(Exception):
    pass


class ProxyConnectError(Exception):
    pass


class SimpleReceiver(protocol.Protocol):
    """Receiver that reads data from  a response"""

    def __init__(self, d):
        self.buf = ''
        self.d = d

    def dataReceived(self, data):
        self.buf += data

    def connectionLost(self, reason):
        self.d.callback(self.buf)


class ScientiaMobileCloudHandler(WurflHandler):

    SMCLOUD_CONFIG = {
        'url': 'http://api.wurflcloud.com/v1/json/',
        'client_version': 'Device-Proxy/0.1'
    }

    def validate_config(self, config):
        # The parent methods configures cache as well as the name where
        # the upstream headers should be stored.
        super(ScientiaMobileCloudHandler, self).validate_config(config)
        if self.cache_lifetime > 86400:
            warnings.warn('Caching for more than 24 hours is against \
                           Scientia Mobiles terms of service.')
        self.smcloud_api_key = config.get('smcloud_api_key')
        if self.smcloud_api_key is None:
            raise Exception('smcloud_api_key config option is required')
        self.http_proxy_host = config.get('http_proxy_host')
        self.http_proxy_port = config.get('http_proxy_port')
        self.http_proxy_username = config.get('http_proxy_username')
        self.http_proxy_password = config.get('http_proxy_password')

    @inlineCallbacks
    def setup_handler(self):
        yield self.connect_to_memcached(
            **self.memcached_config)
        self.namespace = yield self.get_namespace()
        returnValue(self)

    @inlineCallbacks
    def handle_request_and_cache(self, cache_key, user_agent, request):
        expireTime = self.cache_lifetime
        headers = self.handle_user_agent(user_agent)
        if headers is None:
            try:
                device = yield self.get_device_from_smcloud(user_agent)
            except ScientiaMobileCloudHandlerConnectError:
                # Set a short expiry time in case of network error
                device = {}
                expireTime = 60
            headers = self.handle_device(request, device)
        yield self.memcached.set(cache_key, json.dumps(headers),
                                 expireTime=expireTime)
        returnValue(headers)

    @inlineCallbacks
    def get_device_from_smcloud(self, user_agent):
        """
        Queries ScientiaMobile's API and returns a dictionary of the device.
        """
        # Create basic auth string
        b64 = base64.encodestring(self.smcloud_api_key).strip()
        if self.http_proxy_host:
            headers = {
                'X-Cloud-Client': [self.SMCLOUD_CONFIG['client_version']],
                'Authorization': ['Basic %s' % b64],
                'User-Agent': [str(user_agent)],
            }
            if self.http_proxy_username and self.http_proxy_password:
                auth = base64.encodestring(
                    '%s:%s' % (
                        self.http_proxy_username, self.http_proxy_password
                    )
                ).strip()
                # Cater for many proxy servers
                headers['Proxy-Authorization'] = ['Basic %s' % auth]
                headers['Proxy-Authenticate'] = ['Basic %s' % auth]
                headers['Proxy-Authentication'] = ['Basic %s' % auth]
            endpoint = TCP4ClientEndpoint(
                reactor, self.http_proxy_host, self.http_proxy_port or 80,
                timeout=5
            )
            agent = ProxyAgent(endpoint)
            response = yield agent.request('GET', self.SMCLOUD_CONFIG['url'],
                headers=Headers(headers))
            if response.code != 200:
                raise ProxyConnectError()
            d = Deferred()
            response.deliverBody(SimpleReceiver(d))
            body = yield d
        else:
            headers = {
                'X-Cloud-Client': self.SMCLOUD_CONFIG['client_version'],
                'Authorization': 'Basic %s' % b64
            }
            try:
                body = yield getPage(self.SMCLOUD_CONFIG['url'], headers=headers,
                    agent=user_agent, timeout=5)
            except ConnectError, exc:
                raise ScientiaMobileCloudHandlerConnectError(exc)
        device = json.loads(body)
        returnValue(device)

    def handle_device(self, request, device):
        raise NotImplementedError("Subclasses should implement this")
