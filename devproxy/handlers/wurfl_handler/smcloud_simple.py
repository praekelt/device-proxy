from devproxy.handlers.wurfl_handler.smcloud import SMCloudHandler


class SimpleSMCloudHandler(SMCloudHandler):

    def handle_device(self, request, device):
        if device['id'] == 'apple_iphone_ver2_2_1':
            return [{self.header_name: 'high'}]
        else:
            return [{self.header_name: 'medium'}]
