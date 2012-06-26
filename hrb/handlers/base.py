class BaseHandler(object):

    def __init__(self, config):
        self.validate_config(config)

    def validate_config(self, config):
        pass

    def setup_handler(self):
        pass

    def teardown_handler(self):
        pass
