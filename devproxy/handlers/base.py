from twisted.internet import defer


class BaseHandler(object):

    def __init__(self, config):
        self.validate_config(config)

    def validate_config(self, config):
        pass

    def setup_handler(self):
        return defer.succeed(self)

    def teardown_handler(self):
        pass
