from devproxy.handlers.wurfl_handler.base import WurflHandler


class SimpleWurflHandler(WurflHandler):

    def handle_device(self, request, device):
        if device.resolution_width <= 240:
            return [{self.header_name: 'medium'}]
        else:
            return [{self.header_name: 'high'}]


class SimpleWurflTestHandler(SimpleWurflHandler):
    """Handler used in tests. Do not use in production."""

    def handle_user_agent(self, user_agent):
        if user_agent == 'Some special bot':
            return [{self.header_name: 'bot'}]
        return None
