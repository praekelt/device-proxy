from twisted.internet import defer


class Cookie(object):

    encoding = 'utf-8'

    def __init__(self, key, value, expires=None, domain=None, path=None,
                    max_age=None, comment=None, secure=None):
        self.key = key.encode(self.encoding)
        self.value = value.encode(self.encoding)
        self.expires = expires.encode(self.encoding) if expires else None
        self.domain = domain.encode(self.encode) if domain else None
        self.path = path.encode(self.encode) if path else None
        self.max_age = max_age.encode(self.encode) if max_age else None
        self.comment = comment.encode(self.encode) if comment else None
        self.secure = secure.encode(self.encode) if secure else None

    def get_params(self):
        return {
            'expires': self.expires,
            'domain': self.domain,
            'path': self.path,
            'max_age': self.max_age,
            'comment': self.comment,
            'secure': self.secure,
        }


class BaseHandler(object):

    def __init__(self, config):
        self.validate_config(config)

    def validate_config(self, config):
        pass

    def setup_handler(self):
        return defer.succeed(self)

    def teardown_handler(self):
        pass

    def get_headers(self, request):
        """
        Generate the headers that are to be inserted before proxying upstream

        Should return a Dict of valid HTTP Header key, value pairs.
        """
        raise NotImplementedError('Subclasses should implement this.')

    def get_cookies(self, request):
        """
        Generate the a list of cookies that are to be inserted before returning
        the upstream response back to the client.

        Should return a list of `Cookie` instances.
        """
        raise NotImplementedError('Subclasses should implement this.')

    def get_debug_info(self, request):
        """
        Return the debug information for this handler.
        """
        return defer.succeed('')
