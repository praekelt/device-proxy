import base64
import json

from devproxy.handlers.wurfl_handler.base import WurflHandler
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.web.client import getPage


class SMCloudWurflHandler(WurflHandler):

    SMCLOUD_CONFIG = {
        'url': 'http://api.wurflcloud.com/v1/json/',
        'client_version': 'Device-Proxy/0.1'
    }

    def validate_config(self, config):
        # The parent methods configures cache as well as the name where
        # the upstream headers should be stored.
        super(SMCloudWurflHandler, self).validate_config(config)
        # the api key is required, should I raise an exception to say so?
        self.smcloud_api_key = config.get('smcloud_api_key')

    @inlineCallbacks
    def setup_handler(self):
        self.memcached = yield self.connect_to_memcached(
            **self.memcached_config)
        self.namespace = yield self.get_namespace()
        returnValue(self)

    @inlineCallbacks
    def handle_request_and_cache(self, cache_key, user_agent, request):
        device = yield self.get_device_from_smcloud(user_agent)
        headers = self.handle_device(request, device)
        yield self.memcached.set(cache_key, json.dumps(headers),
            expireTime=self.cache_lifetime)
        returnValue(headers)

    @inlineCallbacks
    def get_device_from_smcloud(self, user_agent):
        """
        Queries ScientiaMobile's API and returns a dictionary of the device.
        """
        # create basic auth string
        b64 = base64.encodestring(self.smcloud_api_key).strip()
        headers = {
            'User-Agent': user_agent,
            'X-Cloud-Client': self.SMCLOUD_CONFIG['client_version'],
            'Authorization': 'Basic %s' % b64
        }
        page = yield getPage(self.SMCLOUD_CONFIG['url'], headers=headers,
                             agent=user_agent)
        device = json.loads(page)
        returnValue(device)

    def handle_device(self, request, device):
        #raise NotImplementedError("Subclasses should implement this")
        if device['id'] == 'apple_iphone_ver2_2_1':
            return [{self.header_name: 'high'}]
        else:
            return [{self.header_name: 'medium'}]

    def get_debug_info(self, request):
        user_agent = unicode(request.getHeader('User-Agent') or '')
        device = get_device_from_smcloud(user_agent)
        return flattenString(None, debug.DebugElement(device))
