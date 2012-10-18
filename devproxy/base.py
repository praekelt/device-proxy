from twisted.internet import defer, reactor
from twisted.internet.defer import DeferredList
from twisted.python import log


class BaseRequestHandler(object):

    def setup_handlers(self, handlers):
        self._ready = False
        self.request_handlers = []
        self.handlers_ready = DeferredList(handlers)
        self.handlers_ready.addCallback(self.init_request_handler)

    def init_request_handler(self, handlers):
        for success, handler in handlers:
            if success:
                self.request_handlers.append(handler)
            else:
                reactor.stop()
        self._ready = True
        return self.request_handlers

    def defer_handler(self, handler, args):
        d = defer.Deferred()
        d.addCallback(handler.handle_request)
        d.addErrback(log.err)
        reactor.callLater(0, d.callback, args)
        return d
