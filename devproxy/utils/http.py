from zope.interface import implements
from twisted.internet import defer
from twisted.internet.defer import succeed
from twisted.internet import reactor, protocol
from twisted.web.client import Agent, ResponseDone
from twisted.web.http_headers import Headers
from twisted.web.iweb import IBodyProducer
from twisted.web.http import PotentialDataLoss


def mkheaders(headers):
    """
    Turn a dict of HTTP headers into an instance of Headers.

    Twisted expects a list of values, not a single value. We should
    support both.
    """
    raw_headers = {}
    for k, v in headers.iteritems():
        if isinstance(v, basestring):
            v = [v]
        raw_headers[k] = v
    return Headers(raw_headers)


class StringProducer(object):
    """
    For various twisted.web mechanics we need a producer to produce
    content for HTTP requests, this is a helper class to quickly
    create a producer for a bit of content
    """
    implements(IBodyProducer)

    def __init__(self, body):
        self.body = body
        self.length = len(body)

    def startProducing(self, consumer):
        consumer.write(self.body)
        return succeed(None)

    def pauseProducing(self):
        pass

    def stopProducing(self):
        pass


class SimplishReceiver(protocol.Protocol):
    def __init__(self, response):
        self.deferred = defer.Deferred()
        self.response = response
        self.response.delivered_body = ''
        if response.code == 204:
            self.deferred.callback(self.response)
        else:
            response.deliverBody(self)

    def dataReceived(self, data):
        self.response.delivered_body += data

    def connectionLost(self, reason):
        if reason.check(ResponseDone):
            self.deferred.callback(self.response)
        elif reason.check(PotentialDataLoss):
            # This is only (and always!) raised if we have an HTTP 1.0 request
            # with no Content-Length.
            # See http://twistedmatrix.com/trac/ticket/4840 for sadness.
            #
            # We ignore this and treat the call as success. If we care about
            # checking for potential data loss, we should do that in all cases
            # rather than trying to figure out if we might need to.
            self.deferred.callback(self.response)
        else:
            self.deferred.errback(reason)


def request(url, data=None, headers={}, method='POST'):
    agent = Agent(reactor)
    d = agent.request(method,
                      url,
                      mkheaders(headers),
                      StringProducer(data) if data else None)
    def handle_response(response):
        return SimplishReceiver(response).deferred

    d.addCallback(handle_response)
    return d
