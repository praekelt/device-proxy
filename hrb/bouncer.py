from twisted.internet import reactor, defer
from twisted.web.resource import Resource
from twisted.web.server import NOT_DONE_YET


class BounceResource(Resource):

    isLeaf = True

    def __init__(self, config):
        self.config = config
        Resource.__init__(self)

    def render(self, request):
        d = defer.Deferred()
        d.addCallback(self.render_result, request)
        reactor.callLater(0, d.callback, "hello")
        return NOT_DONE_YET

    def render_result(self, response, request):
        request.write(response)
        request.finish()
