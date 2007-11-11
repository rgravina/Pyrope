from zope.interface import implements, Interface, Attribute
from twisted.spread import pb
from twisted.python import log
from twisted.internet.defer import inlineCallbacks

#eskimoapps imports
#from eskimoapps.utils.pbutil import ObservedCacheable
import random

class IApplication(Interface):
    """A Pyrope application"""
    def start(self, perspective):
        """Start up the application"""

class Application(pb.Viewable):
    implements(IApplication)
    def __init__(self, name, description=None):
        self.name = name
        self.description = description
        self.users = []    #i.e. users (perspectives) running this application
        self.widgets = {}    #map id -> widget
    def view_startApplication(self, perspective, handler):
        """Called by the client when a user wants to start up a new application."""
        #save the perspective for later use
        #TODO: make sure perspective is removed when app is closed
        self.users.append(perspective)
        #simply call the start method
        self.start(handler)
    def view_shutdownApplication(self, perspective, handler):
        """Called by the client when a user wants to shutdown the application."""
        self.users.remove(perspective)
        #simply call the start method
        self.shutdown(handler)
    def start(self, handler):
        """Subclasses should start their applications here"""
        pass
    def shutdown(self, handler):
        """Subclasses should put any shitdown code here"""
        pass
    def view_createdFrame(self, perspective, remote, id):
        print "created frame"
        widget = self.widgets[id]
        widget.remote = remote

class Window(pb.Copyable, pb.RemoteCopy):
    def __init__(self, app, handler, parent):
        self.id = random.random()
        #TODO: figure out a way to not have to always pass the perspective as the first argument
        self.app = app
        app.widgets[self.id] = self
        self.handler = handler
        self.parent = parent
        self.remote = None
    def getStateToCopy(self):
        d = self.__dict__.copy()
        if self.parent:
            d["parent"] = self.parent.id
        del d["handler"]
        del d["remote"]
        return d
pb.setUnjellyableForClass(Window, Window)

#class BoxSizer(pb.Copyable, pb.RemoteCopy):
#    def __init__(self, perspective):
#        self.id = random.random()
#        self.perspective = perspective    
#        perspective.createBoxSizer(self)
#pb.setUnjellyableForClass(BoxSizer, BoxSizer)
#
#class Panel(Window):
#    def __init__(self, perspective, parent):
#        Window.__init__(self, perspective, parent)
#        perspective.createPanel(self)
#pb.setUnjellyableForClass(Panel, Panel)
#
class Frame(Window):
    def __init__(self, app, handler, parent, title=u""):
        Window.__init__(self, app, handler, parent)
        self.title = title
    def setup(self):
        return self.handler.callRemote("createFrame", self)
    def show(self):
        return self.remote.callRemote("show")

pb.setUnjellyableForClass(Frame, Frame)

#class Button(Window):
#    CLICK = range(1) #python enum hack
#    def __init__(self, perspective, parent, label=u""):
#        Window.__init__(self, perspective, parent)
#        self.label = label
#        self.handler = None
#        perspective.createButton(self)
#    def bind(self, event, handlerFunction):
#        self.handler = handlerFunction
#pb.setUnjellyableForClass(Button, Button)
#
#class Notebook(Window):
#    def __init__(self, perspective, parent):
#        Window.__init__(self, perspective, parent)
#        perspective.createNotebook(self)
#    def addPage(self, panel, title):
#        self.perspective.addPage(self.id, panel.id, title)
#pb.setUnjellyableForClass(Notebook, Notebook)

