from devproxy.handlers.wurfl_handler.scientia_mobile_cloud import ScientiaMobileCloudHandler


class ScientiaMobileCloudResolutionHandler(ScientiaMobileCloudHandler):

    def handle_device(self, request, device):
        # check resolution:
        if device['id'] == 'apple_iphone_ver2_2_1':
            return [{self.header_name: 'high'}]
        else:
            return [{self.header_name: 'medium'}]
