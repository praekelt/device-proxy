from twisted.internet import defer, reactor
from twisted.web.resource import Resource
from twisted.web.server import NOT_DONE_YET
from twisted.internet.defer import DeferredList
from twisted.python import log


class BounceResource(Resource):

    isLeaf = True

    def __init__(self, handlers):
        self._ready = False
        self.request_handlers = []
        self.handlers_ready = DeferredList(handlers)
        self.handlers_ready.addCallback(self.init_resource)
        Resource.__init__(self)

    def init_resource(self, results):
        for success, handler in results:
            if success:
                self.request_handlers.append(handler)
            else:
                reactor.stop()
        self._ready = True
        return self.request_handlers

    def defer_handler(self, handler, request):
        d = defer.Deferred()
        d.addCallback(handler.handle_request)
        d.addErrback(log.err)
        reactor.callLater(0, d.callback, request)
        return d

    def process_request(self, request):
        deferreds = [self.defer_handler(handler, request) for
                        handler in self.request_handlers]
        dl = defer.DeferredList(deferreds)
        dl.addCallback(self.process_result, request)
        return dl

    def process_result(self, result, request):
        response = ''.join([value for (success, value) in result if value])
        self.render_result(request, response)

    def render(self, request):
        if self._ready:
            self.process_request(request)
            return NOT_DONE_YET
        else:
            return 'Waiting on handlers to start.'

    def render_result(self, request, response):
        request.setHeader('Location', request.uri)
        request.write(response)
        request.finish()
