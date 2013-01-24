from devproxy.handlers.wurfl_handler.base import WurflHandler


class SimpleWurflHandler(WurflHandler):

    def handle_device(self, request, device):
        if device.resolution_width <= 240:
            return [{self.header_name: 'medium'}]
        else:
            return [{self.header_name: 'high'}]
