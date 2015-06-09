import base64
import json
import warnings
from urllib import urlencode

from devproxy.handlers.wurfl_handler.base import WurflHandler
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.internet import reactor
from twisted.internet.endpoints import HostnameEndpoint
from twisted.web.client import ProxyAgent, getPage

class ScientiaMobileCloudHandlerConnectError(Exception):
    pass


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
        # create basic auth string
        b64 = base64.encodestring(self.smcloud_api_key).strip()
        headers = {
            'X-Cloud-Client': self.SMCLOUD_CONFIG['client_version'],
            'Authorization': 'Basic %s' % b64
        }
        if self.http_proxy_host:
            if self.http_proxy_username and self.http_proxy_password:
                auth = base64.encodestring(
                    '%s:%s' % (
                        self.http_proxy_username, self.http_proxy_password
                    ).strip()
                )
                headers['Proxy-Authorization'] = ['Basic ' + auth]
            endpoint = HostnameEndpoint(
                reactor, self.http_proxy_host, self.http_proxy_port or 80
            )
            agent = ProxyAgent(endpoint)
            qs = urlencode({'agent': user_agent})
            page = yield agent.request('GET', self.SMCLOUD_CONFIG['url'] + '?' + qs,
                headers=headers)
        else:
            try:
                page = yield getPage(self.SMCLOUD_CONFIG['url'], headers=headers,
                    agent=user_agent, timeout=5)
            except ConnectError, exc:
                raise ScientiaMobileCloudHandlerConnectError(exc)
        device = json.loads(page)
        returnValue(device)

    def handle_device(self, request, device):
        raise NotImplementedError("Subclasses should implement this")
