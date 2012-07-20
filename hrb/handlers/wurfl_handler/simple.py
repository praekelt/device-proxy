from hrb.handlers.wurfl_handler.base import WurflHandler


class SimpleWurflHandler(WurflHandler):

    def handle_device(self, request, device):
        if device.resolution_width <= 240:
            request.addCookie(self.cookie_name, 'medium')
        else:
            request.addCookie(self.cookie_name, 'high')

    def debug_device(self, request, device, user_agent):
        #print device.fall_back
        return ("""
        <html>
        <body>
            <b>Matched Device:</b> %(device_name)s<br/>
            <b>Fallback device:</b> %(fallback)s<br/>
            <b>Resolution:</b> %(width)s x %(height)s<br/><br/>
            <b>User agent:</b> %(ua)s<br/>
        </body>
        </html>
        """ % {'device_name': device.devid,
                'fallback': device.fall_back,
                'width': device.resolution_width,
                'height': device.resolution_height,
                'ua': user_agent,
            }).encode('utf-8')
