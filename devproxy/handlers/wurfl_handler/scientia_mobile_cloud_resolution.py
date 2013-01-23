from devproxy.handlers.wurfl_handler.scientia_mobile_cloud \
    import ScientiaMobileCloudHandler


class ScientiaMobileCloudResolutionHandler(ScientiaMobileCloudHandler):

    def handle_device(self, request, device):
        if device['capabilities']['resolution_width'] > 240:
            return [{self.header_name: 'high'}]
        else:
            return [{self.header_name: 'medium'}]
