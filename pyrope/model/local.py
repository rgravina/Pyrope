import wx
from zope.interface import implements, Interface, Attribute
from twisted.spread import pb
from twisted.python import log
from twisted.internet.defer import inlineCallbacks
from pyrope.model.shared import *
from pyrope.errors import RemoteResourceNotCreatedException

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
    def view_createdWindow(self, perspective, remote, id):
        widget = self.widgets[id]
        widget.remote = remote
    def view_event(self, perspective, id, event):
        widget = self.widgets[id]
        widget.handlers[event](widget)

class Window(pb.Copyable, pb.RemoteCopy):
    def __init__(self, app, handler, parent, position=DefaultPosition, size=DefaultSize):
        self.id = random.random()
        #TODO: figure out a way to not have to always pass the perspective as the first argument
        #TODO: styles
        self.app = app
        app.widgets[self.id] = self
        self.handler = handler
        self.parent = parent
        self.position = position
        self.size = size
        self._appliedStyles = []
        self._removedStyles = []
        #the remote reference will be set when the client supplies it
        self.remote = None
        #for event handling
        self.handlers = {}
    def createRemote(self):
        return self.handler.callRemote("createWindow", self)
    def addStyle(self, style):
        self._appliedStyles.append(style)
        if style in self._removedStyles:
            self._removedStyles.remove(style)
    def removeStyle(self, style):
        self._removedStyles.append(style)
        if style in self._appliedStyles:
            self._appliedStyles.remove(style)
    def getStateToCopy(self):
        d = self.__dict__.copy()
        if self.parent:
            d["parent"] = self.parent.id
        d["style"] = 0
        for style in self._appliedStyles:
            d["style"] = d["style"] | constants[style]
        for style in self._removedStyles:
            d["style"] = d["style"] ^ constants[style]
        #we don't need to send these objects to the client (and can't anyway)
        d["handlers"] = []
        for event, fn in self.handlers.items():
            d["handlers"].append(event)
        del d["remote"]
        return d
    def callRemote(self, functName, *args):
        if self.remote:
            return self.remote.callRemote(functName, *args)
        else:
            raise RemoteResourceNotCreatedException, "You must call createRemote before calling this method"
    def bind(self, event, handlerFunction):
        self.handlers[event] = handlerFunction
    def clientToScreen(self, point):
        return self.callRemote("clientToScreen", point)

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
    def __init__(self, app, handler, parent, title=u"", position=DefaultPosition, size=DefaultSize):
        Window.__init__(self, app, handler, parent, position=position, size=size)
        self.title = title
    def getStateToCopy(self):
        d = Window.getStateToCopy(self)
        #if no styles have been added or remove, apply the default style
        if not self._appliedStyles and not self._removedStyles:
            d["style"] =  d["style"] | constants[DefaultFrameStyle]
        return d
    def createRemote(self):
        return self.handler.callRemote("createFrame", self)
    def show(self):
        return self.callRemote("show")
    def centre(self, direction=wx.BOTH, centreOnScreen=False):
        return self.callRemote("centre", direction, centreOnScreen)
    def destroy(self):
        return self.callRemote("destroy")
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

