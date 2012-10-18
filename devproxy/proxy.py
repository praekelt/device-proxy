from urllib import quote as urlquote

from twisted.internet import defer
from twisted.web import proxy, server, http


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
        return server.NOT_DONE_YET

    @defer.inlineCallbacks
    def call_handlers(self, request):
        for handler in self.handlers:
            headers = (yield handler.get_headers(request)) or []
            for header in headers:
                for key, value in header.items():
                    request.requestHeaders.addRawHeader(
                        key.encode(self.encoding), value.encode(self.encoding))

            cookies = (yield handler.get_cookies(request)) or []
            for cookie in cookies:
                request.addCookie(cookie.key, cookie.value,
                    **cookie.get_params())

        proxy.ReverseProxyResource.render(self, request)


class ProxySiteException(Exception):
    pass


class ProxySite(server.Site):

    resourceClass = ReverseProxyResource

    def __init__(self, config, *args, **kwargs):
        http.HTTPFactory.__init__(self, *args, **kwargs)
        self.sessions = {}

        handlers = []
        for handler_config in config['handlers']:
            [(name, class_path)] = handler_config.items()
            parts = class_path.split('.')
            module = '.'.join(parts[:-1])
            class_name = parts[-1]
            handler_module = __import__(module, fromlist=[class_name])
            handler_class = getattr(handler_module, class_name)
            handler = handler_class(config[name])
            handlers.append(handler)

        upstream = config['upstream']
        self.upstream_host, self.upstream_port = upstream.split(':', 1)
        self.path = config.get('path', '')
        self.handlers = handlers

    def startFactory(self):
        server.Site.startFactory(self)
        d = defer.DeferredList([h.setup_handler() for h in self.handlers])
        d.addCallback(self.setup_resource)
        return d

    def setup_resource(self, results):
        started_handlers = []
        for success, handler in results:
            if success:
                started_handlers.append(handler)
            else:
                raise ProxySiteException(handler.value)

        self.resource = self.resourceClass(started_handlers,
            self.upstream_host, int(self.upstream_port), self.path)
