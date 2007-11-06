from zope.interface import implements, Interface, Attribute
from twisted.spread import pb
from twisted.python import log
#eskimoapps imports
#from eskimoapps.utils.pbutil import ObservedCacheable
import random

class Application(pb.Viewable):
    def __init__(self, name, handler=None, description=None):
        self.name = name
        self.description = description
        self.handler = handler
        if not self.handler:
            self.handler = ApplicationHandler()
    def view_startApplication(self, perspective):
        self.handler.start(perspective)

class IApplicationHandler(Interface):
    """A Pyrope application"""
    def start(self):
        """Start up the application"""

class ApplicationHandler(object):
    implements(IApplicationHandler)
    def start(self):
        log.msg("Starting up default application handler.")

class Window(pb.Copyable, pb.RemoteCopy):
    def __init__(self, perspective, parent):
        self.id = random.random()
        self.perspective = perspective    
        self.parent = parent    
pb.setUnjellyableForClass(Window, Window)

class Frame(Window):
    def __init__(self, perspective, parent, title=u""):
        Window.__init__(self, perspective, parent)
        self.title = title
        #tell the client to create a wxFrame
        perspective.createFrame(self)
    def show(self):
        self.perspective.show(self.id)
pb.setUnjellyableForClass(Frame, Frame)

class Label(Window):
    def __init__(self, perspective, parent, text=u""):
        Window.__init__(self, perspective, parent)
        self.text = text
        perspective.createLabel(self)
pb.setUnjellyableForClass(Label, Label)
