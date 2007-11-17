import wx
from zope.interface import implements, Interface, Attribute
from twisted.spread import pb
from twisted.python import log
#from twisted.internet.defer import inlineCallbacks
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
    def view_updateWidgetRemoteReference(self, perspective, remote, id):
        widget = self.widgets[id]
        widget.remote = remote
    def view_handleEvent(self, perspective, id, event):
        widget = self.widgets[id]
        widget.eventHandlers[event](widget)

class Window(pb.Copyable, pb.RemoteCopy):
    def __init__(self, app, handler, parent, position=DefaultPosition, size=DefaultSize, style=0):
        self.id = random.random()
        #TODO: figure out a way to not have to always pass the perspective as the first argument
        #TODO: styles
        self.app = app
        app.widgets[self.id] = self
        self.handler = handler
        self.parent = parent
        self.position = position
        self.size = size
        self.style = style
        #the remote reference will be set when the client supplies it
        self.remote = None
        #for event handling
        self.eventHandlers = {}
    def createRemote(self):
        return self.handler.callRemote("createWidget", self)
    def getStateToCopy(self):
        d = self.__dict__.copy()
        if self.parent:
            d["parent"] = self.parent.id
        del d["handler"]
        d["eventHandlers"] = []
        for event, fn in self.eventHandlers.items():
            d["eventHandlers"].append(event)
        del d["remote"]
        return d
    def callRemote(self, functName, *args):
        if self.remote:
            return self.remote.callRemote(functName, *args)
        else:
            raise RemoteResourceNotCreatedException, "You must call createRemote before calling this method"
    def bind(self, event, handlerFunction):
        self.eventHandlers[event] = handlerFunction
    def ClientToScreen(self, point):
        return self.callRemote("ClientToScreen", point)
    def Show(self):
        return self.callRemote("Show")
    def Centre(self, direction=wx.BOTH, centreOnScreen=False):
        return self.callRemote("Centre", direction, centreOnScreen)
    def Destroy(self):
        return self.callRemote("Destroy")

pb.setUnjellyableForClass(Window, Window)
#
class Frame(Window):
    def __init__(self, app, handler, parent, title=u"", position=DefaultPosition, size=DefaultSize, style=wx.DEFAULT_FRAME_STYLE):
        Window.__init__(self, app, handler, parent, position=position, size=size, style=style)
        self.title = title
pb.setUnjellyableForClass(Frame, Frame)

class Dialog(Window):
    def __init__(self, app, handler, parent, title=u"", position=DefaultPosition, size=DefaultSize, style=wx.DEFAULT_DIALOG_STYLE):
        Window.__init__(self, app, handler, parent, position=position, size=size, style=style)
        self.title = title
    def ShowModal(self):
        return self.callRemote("ShowModal")
pb.setUnjellyableForClass(Dialog, Dialog)

class MessageDialog(Dialog):
    def __init__(self, app, handler, parent, message, caption=u"Message Box", position=DefaultPosition, size=DefaultSize, style=wx.OK | wx.CANCEL):
        Dialog.__init__(self, app, handler, parent, title=caption, position=position, size=size, style=style)
        self.message = message
pb.setUnjellyableForClass(MessageDialog, MessageDialog)

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

