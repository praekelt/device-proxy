from twisted.python import log
from twisted.web.resource import Resource
from twisted.web.server import NOT_DONE_YET
from twisted.internet import defer


class BounceResource(Resource):

    isLeaf = True
    encoding = 'utf-8'

    def __init__(self, handlers):
        self.handlers = handlers

    def render(self, request):
        self.call_handlers(request)
        return NOT_DONE_YET

    def call_handlers(self, request):
        deferreds = [handler.get_headers(request) for
                        handler in self.handlers]
        dl = defer.DeferredList(deferreds)
        dl.addCallback(self.process_result, request)
        return dl

    def process_result(self, result, request):
        for success, data in result:
            if not success:
                log.err(data)
            else:
                # here `data` is the headers dict returned by the handlers
                for key, value in data.items():
                    request.setHeader(key.encode(self.encoding),
                                        value.encode(self.encoding))
        request.finish()
