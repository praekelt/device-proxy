import yaml

from zope.interface import implements

from twisted.python import usage
from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker
from twisted.application import internet

from devproxy.proxy import ProxySite


class Options(usage.Options):
    optParameters = [
        ["config", "c", "config.yaml", "The handlers config file"],
    ]


class BouncerServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = "devproxy"
    description = "Device Proxy. A reverse HTTP Proxy that can inspect and " \
                    "manipulate HTTP Headers before sending upstream."
    options = Options

    def makeService(self, options):
        config_file = options['config']
        with open(config_file, 'r') as fp:
            config = yaml.safe_load(fp)

        port = config.pop('port', 8025)

        return internet.TCPServer(int(port),
            ProxySite(config))

serviceMaker = BouncerServiceMaker()
