from twisted.internet import defer, reactor
from twisted.web.resource import Resource
from twisted.web.server import NOT_DONE_YET
from twisted.python import log


class BounceResource(Resource):

    isLeaf = True

    def __init__(self, request_handlers):
        self.request_handlers = request_handlers
        Resource.__init__(self)

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
        self.process_request(request)
        return NOT_DONE_YET

    def render_result(self, request, response):
        request.write(response)
        request.finish()
