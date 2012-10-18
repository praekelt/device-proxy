from twisted.web.template import Element, TagLoader, renderer, XMLFile
from twisted.python.filepath import FilePath
from pywurfl import RootDevice


class DebugElement(Element):
    loader = XMLFile(FilePath('devproxy/templates/debug.xml'))

    def __init__(self, device, loader=None):
        self.device = device
        super(DebugElement, self).__init__(loader=loader)

    @renderer
    def render_device(self, request, tag):
        return tag.fillSlots(user_agent=self.device.devua,
            wurfl_id=self.device.devid)

    @renderer
    def render_fallbacks(self, request, tag):
        base_class = self.device.__class__.__bases__[0]
        while base_class is not RootDevice:
            yield tag.clone().fillSlots(fallback=base_class.devid)
            base_class = base_class.__bases__[0]

    @renderer
    def render_capabilities(self, request, tag):
        for group in self.device.groups.keys():
            tag.fillSlots(group=group.title())
            yield DebugCapabilityElement(self.device, group,
                loader=TagLoader(tag))

    @renderer
    def render_shortcuts(self, request, tag):
        for group in self.device.groups.keys():
            yield tag.clone().fillSlots(group=group.title())


class DebugCapabilityElement(Element):

    def __init__(self, device, group, loader=None):
        self.device = device
        self.group = group
        super(DebugCapabilityElement, self).__init__(loader=loader)

    @renderer
    def render_capability(self, request, tag):
        for cap in sorted(self.device.groups[self.group]):
            attr = getattr(self.device, cap)
            yield tag.clone().fillSlots(property=cap, value=unicode(attr))
