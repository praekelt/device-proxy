from devproxy.handlers.wurfl_handler.scientia_mobile_cloud \
    import ScientiaMobileCloudHandler


class ScientiaMobileCloudResolutionHandler(ScientiaMobileCloudHandler):

    def handle_device(self, request, device):
        if device['capabilities']['resolution_width'] > 240:
            return [{self.header_name: 'high'}]
        else:
            return [{self.header_name: 'medium'}]


class ScientiaMobileCloudResolutionTouchHandler(ScientiaMobileCloudHandler):

    def handle_device(self, request, device):
        result = {self.header_name: self.default_ua_map}

        is_web_browser = True
        is_smart_browser = False
        try:
            is_web_browser = device['capabilities']['ux_full_desktop'] \
                or device['capabilities']['is_tablet']
            is_smart_browser = \
                (device['capabilities']['resolution_width'] >= 320) \
                and (device['capabilities']['pointing_method'] == 'touchscreen')
            is_basic_browser = not (is_web_browser or is_smart_browser)
        except KeyError:
            pass

        if is_web_browser:
            result[self.header_name] = 'web'
        elif is_smart_browser:
            result[self.header_name] = 'smart'
        elif is_basic_browser:
            result[self.header_name] = 'basic'

        return [result]
