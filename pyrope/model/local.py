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
    def view_handleEvent(self, perspective, id, event, data=None):
        widget = self.widgets[id]
        if event == EventText:
            widget._value = data
        widget.eventHandlers[event](widget)
    def view_updateRemote(self, perspective, id, remote):
        widget = self.widgets[id]
        widget.remote = remote
        print widget
        
class PyropeWidget(pb.Copyable, pb.RemoteCopy):
    def __init__(self, app, handler):
        self.id = random.random()
        #TODO: figure out a way to not have to always pass the perspective as the first argument
        self.app = app
        app.widgets[self.id] = self
        self.handler = handler
        #the remote reference will be set when the client supplies it
        self.remote = None
        #for event handling
        self.eventHandlers = {}
    @inlineCallbacks
    def createRemote(self):
        #creates remote widget, and gets a pb.RemoteReference to it's client-side proxy
        self.remote = yield self.handler.callRemote("createWidget", self)
    def callRemote(self, functName, *args):
        if self.remote:
            return self.remote.callRemote(functName, *args)
        else:
            raise RemoteResourceNotCreatedException, "You must call createRemote before calling this method"
    def bind(self, event, handlerFunction):
        self.eventHandlers[event] = handlerFunction

class Window(PyropeWidget):
    def __init__(self, app, handler, parent, position=DefaultPosition, size=DefaultSize, style=0):
        PyropeWidget.__init__(self, app, handler)
        self.parent = parent
        self.position = position
        self.size = size
        self.style = style
        #other props
        self._backgroundColour = None
        self.sizer = None
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
    def ClientToScreen(self, point):
        return self.callRemote("ClientToScreen", point)
    def Hide(self):
        return self.callRemote("Hide")
    def Show(self):
        return self.callRemote("Show")
    def Centre(self, direction=wx.BOTH, centreOnScreen=False):
        return self.callRemote("Centre", direction, centreOnScreen)
    def Destroy(self):
        return self.callRemote("Destroy")
    def Disable(self):
        return self.callRemote("Disable")
    def Enable(self):
        return self.callRemote("Enable")

    def GetBackgroundColour(self):
        #simply return the background colour
        return self._backgroundColour
    def SetBackgroundColour(self, colour):
        #set the local background colour
        self._backgroundColour = colour
        #set remote
        return self.callRemote("SetBackgroundColour", colour)
pb.setUnjellyableForClass(Window, Window)

class BoxSizer(PyropeWidget):
    def __init__(self, app, handler, orientation):
        PyropeWidget.__init__(self, app, handler)
        self.orientation = orientation
        self.widgets = []
    def add(self, widget):
        self.widgets.append(widget)
pb.setUnjellyableForClass(BoxSizer, BoxSizer)

class Panel(Window):
    def __init__(self, app, handler, parent, position=DefaultPosition, size=DefaultSize, style=wx.TAB_TRAVERSAL):
        Window.__init__(self, app, handler, parent, position=position, size=size, style=style)
pb.setUnjellyableForClass(Panel, Panel)

class TextBox(Window):
    def __init__(self, app, handler, parent, value=u"", position=DefaultPosition, size=DefaultSize, style=0):
        Window.__init__(self, app, handler, parent, position=position, size=size, style=style)
        self._value = value
    def _getValue(self):
        return self._value
    def setValue(self, value):
        self._value = value
        return self.callRemote("SetValue", value)
    value = property(_getValue)
pb.setUnjellyableForClass(TextBox, TextBox)

class Label(Window):
    def __init__(self, app, handler, parent, value=u"", position=DefaultPosition, size=DefaultSize, style=0):
        Window.__init__(self, app, handler, parent, position=position, size=size, style=style)
        self._value = value
    def _getValue(self):
        return self._value
    def setValue(self, value):
        self._value = value
        return self.callRemote("SetLabel", value)
    value = property(_getValue)
pb.setUnjellyableForClass(Label, Label)

######################
# Frames and Dialogs #
######################

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

