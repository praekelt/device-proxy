# -*- test-case-name: devproxy.tests.test_demo -*-
import collections

from twisted.internet.defer import succeed

from devproxy.handlers.base import BaseHandler, Cookie


class DemoHandler(BaseHandler):

    def validate_config(self, config):
        """
        Raise an error if something in the ``config`` dict isn't
        what you were expecting it to be
        """
        if not isinstance(config.get('cookies'), collections.Mapping):
            raise ValueError('Invalid `cookies` value in the config.')
        self.cookies = config['cookies']

    def setup_handler(self):
        """
        If your handler needs to connect to something external service
        like Memcache, this is where you'd do that.

        Needs to return a Deferred which returns `self`
        """
        return succeed(self)

    def teardown_handler(self):
        """
        If your handler has things that need to be closed down properly.
        Like a socket connection to some external service, this is where
        you'd do that
        """

    def get_headers(self, request):
        """
        Return a list of dictionaries whose keys and values are to be
        inserted into the request before being proxied upstream
        """
        return [{
            'X-Device-Is-Dumb': 'Very'
        }]

    def get_cookies(self, request):
        """
        Return a list of Cookie instances to be inserted into the response
        received from upstream before returning it to the client
        """
        return [Cookie(key, value)
                for key, value in self.cookies.items()]
