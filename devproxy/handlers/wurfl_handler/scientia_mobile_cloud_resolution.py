from devproxy.handlers.wurfl_handler.scientia_mobile_cloud \
    import ScientiaMobileCloudHandler


class ScientiaMobileCloudResolutionHandler(ScientiaMobileCloudHandler):

    def handle_device(self, request, device):
        # ScientiaMobile has changed their API silently once before. Handle any
        # API changes.
        result = {self.header_name: 'high'}
        try:
            if device['capabilities']['resolution_width'] > 240:
                result = {self.header_name: 'high'}
            else:
                result = {self.header_name: 'medium'}
        except KeyError:
            pass
        return [result]
