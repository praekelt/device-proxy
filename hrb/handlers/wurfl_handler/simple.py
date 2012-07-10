from hrb.handlers.wurfl_handler.base import WurflHandler


class SimpleWurflHandler(WurflHandler):

    def handle_device(self, request, device):
        if device.resolution_width <= 240:
            request.addCookie(self.cookie_name, 'medium')
        else:
            request.addCookie(self.cookie_name, 'high')
