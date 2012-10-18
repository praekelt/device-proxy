import yaml

from zope.interface import implements

from twisted.python import usage
from twisted.plugin import IPlugin
from twisted.application.service import IServiceMaker
from twisted.application import internet
from twisted.web.server import Site
from twisted.python import log

from devproxy.bouncer import BounceResource


class Options(usage.Options):
    optParameters = [
        ["config", "c", "config.yaml", "The handlers config file"],
    ]


class BouncerServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = "devproxy"
    description = "Http Request Bouncer, redirects after inspection."
    options = Options

    def makeService(self, options):
        config_file = options['config']
        with open(config_file, 'r') as fp:
            config = yaml.safe_load(fp)

        handlers = []
        for handler_config in config['handlers']:
            [(name, class_path)] = handler_config.items()
            parts = class_path.split('.')
            module = '.'.join(parts[:-1])
            class_name = parts[-1]
            handler_module = __import__(module, fromlist=[class_name])
            handler_class = getattr(handler_module, class_name)
            handler = handler_class(config[name])
            d = handler.setup_handler()
            d.addErrback(log.err)
            handlers.append(d)

        return internet.TCPServer(int(config['port']),
            Site(BounceResource(handlers)))

serviceMaker = BouncerServiceMaker()
