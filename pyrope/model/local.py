from zope.interface import implements, Interface, Attribute
from twisted.spread import pb
from twisted.python import log
#eskimoapps imports
#from eskimoapps.utils.pbutil import ObservedCacheable

class Application(pb.Viewable):
    def __init__(self, name, handler=None, description=None):
        self.name = name
        self.description = description
        self.handler = handler
        if not self.handler:
            self.handler = ApplicationHandler()
    def view_startApplication(self, perspective):
        print perspective
        self.handler.start(perspective)

class IApplicationHandler(Interface):
    """A Pyrope application"""
    def start(self):
        """Start up the application"""

class ApplicationHandler(object):
    implements(IApplicationHandler)
    def start(self):
        log.msg("Starting up default application handler.")

class Window(object):
    def __init__(self, perspective, window):
        self.perspective = perspective    
        self.window = window    

class Frame(Window):
    def __init__(self, perspective, window, title=u""):
        Window.__init__(self, perspective, window)
        self.title = title
        print perspective

