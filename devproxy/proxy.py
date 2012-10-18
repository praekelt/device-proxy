from urllib import quote as urlquote

from twisted.internet import defer
from twisted.web import proxy
from twisted.web.server import NOT_DONE_YET


class ReverseProxyResource(proxy.ReverseProxyResource):

    encoding = 'utf-8'

    def __init__(self, handlers, *args, **kwargs):
        proxy.ReverseProxyResource.__init__(self, *args, **kwargs)
        self.handlers = handlers

    def getChild(self, path, request):
        return ReverseProxyResource(self.handlers, self.host,
            self.port, self.path + '/' + urlquote(path, safe=""), self.reactor)

    def render(self, request):
        self.call_handlers(request)
        return NOT_DONE_YET

    @defer.inlineCallbacks
    def call_handlers(self, request):
        for handler in self.handlers:
            headers = (yield handler.get_headers(request)) or {}
            for header in headers:
                for key, value in headers.items():
                    request.requestHeaders.addRawHeader(
                        key.encode(self.encoding), value.encode(self.encoding))

            cookies = (yield handler.get_cookies(request)) or {}
            for cookie in cookies:
                request.addCookie(cookie.key, cookie.value,
                    **cookie.get_params())

        proxy.ReverseProxyResource.render(self, request)
