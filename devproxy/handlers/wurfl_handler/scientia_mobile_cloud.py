import base64
import json
import warnings

from devproxy.handlers.wurfl_handler.base import WurflHandler
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.web.client import getPage


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
            #User-Agent is set by agent in getPage.
            'X-Cloud-Client': self.SMCLOUD_CONFIG['client_version'],
            'Authorization': 'Basic %s' % b64
        }
        page = yield getPage(self.SMCLOUD_CONFIG['url'], headers=headers,
                             agent=user_agent)
        device = json.loads(page)
        returnValue(device)

    def handle_device(self, request, device):
        raise NotImplementedError("Subclasses should implement this")
