import urlparse
from urllib import quote as urlquote

from twisted.python import log
from twisted.internet import defer, reactor
from twisted.web import proxy, server, http, resource


class ProxyClientFactory(proxy.ProxyClientFactory):
    noisy = False


class DebugResource(resource.Resource):
    isLeaf = True

    def __init__(self, handlers, *args, **kwargs):
        resource.Resource.__init__(self, *args, **kwargs)
        self.handlers = handlers

    def render_GET(self, request):
        self.call_handlers(request)
        return server.NOT_DONE_YET

    @defer.inlineCallbacks
    def call_handlers(self, request):
        for handler in self.handlers:
            debug_info = yield handler.get_debug_info(request)
            request.write(debug_info)
        request.finish()


class HealthResource(resource.Resource):
    isLeaf = True

    def render_GET(self, request):
        return 'OK'


class ReverseProxyResource(proxy.ReverseProxyResource):

    proxyClientFactoryClass = ProxyClientFactory
    encoding = 'utf-8'

    def __init__(self, handlers, debug_path, health_path, *args, **kwargs):
        proxy.ReverseProxyResource.__init__(self, *args, **kwargs)
        self.debug_path = debug_path.lstrip('/')
        self.health_path = health_path.lstrip('/')
        self.handlers = handlers

    def getChild(self, path, request):
        if self.debug_path and path == self.debug_path:
            return DebugResource(self.handlers)
        if self.health_path and path == self.health_path:
            return HealthResource()

        return ReverseProxyResource(self.handlers, '', '', self.host,
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
        self.connect_upstream(request)

    def connect_upstream(self, request):
        """
        Render a request by forwarding it to the proxied server.
        """
        qs = urlparse.urlparse(request.uri)[4]
        if qs:
            rest = self.path + '?' + qs
        else:
            rest = self.path
        clientFactory = self.proxyClientFactoryClass(
            request.method, rest, request.clientproto,
            request.getAllHeaders(), request.content.read(), request)
        self.reactor.connectTCP(self.host, self.port, clientFactory)


class ProxySiteException(Exception):
    pass


class ProxySite(server.Site):

    resourceClass = ReverseProxyResource

    def __init__(self, config, *args, **kwargs):
        # Go straight the server.Site's super, we're essentially doing the same
        # this but we only create `self.resource` when `startWorker()` is
        # completed as that's the first place where we can return a Deferred
        # (which we need to return because the handler loading is async)
        http.HTTPFactory.__init__(self, *args, **kwargs)
        # server.Site uses this internally to manage sessions.
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
        self.debug_path = config.get('debug_path', '')
        self.health_path = config.get('health_path', '')
        self.handlers = handlers

    def startFactory(self):
        server.Site.startFactory(self)
        d = defer.DeferredList([h.setup_handler() for h in self.handlers])
        d.addCallback(self.setup_resource)
        d.addErrback(self.shutdown)
        return d

    def shutdown(self, failure):
        log.err(failure.value)
        reactor.stop()

    def setup_resource(self, results):
        started_handlers = []
        for success, handler in results:
            if success:
                started_handlers.append(handler)
            else:
                raise ProxySiteException(handler.value)

        self.resource = self.resourceClass(started_handlers, self.debug_path,
            self.health_path, self.upstream_host, int(self.upstream_port),
            self.path)
