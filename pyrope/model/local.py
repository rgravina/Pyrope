"""The Local (i.e. usually server-side) model."""
import wx
from zope.interface import implements, Interface, Attribute
from twisted.spread import pb
from twisted.python import log
from twisted.internet.defer import inlineCallbacks
from pyrope.model.shared import *
from pyrope.model.remote import *
from pyrope.errors import RemoteResourceNotCreatedException

class IApplication(Interface):
    """A Pyrope application"""
    def start(self, handler):
        """Start up the application"""

class RunningApplication(object):
    """Represents an instance of a running application.
    At this stage there are no methods, it just acts as a parameter object."""
    def __init__(self, perspective, handler):
        self.perspective = perspective     #users perpective 
        self.handler = handler             #client-side application handler
        self.widgets = []                  #widgets in this instance
    
class Application(pb.Viewable):
    """Base class for user applications. Users should subclass this and override at least L{start}."""
    implements(IApplication)
    def __init__(self, name, description=None):
        self.name = name
        self.description = description
        self.runningApplications = {}
    def view_startApplication(self, perspective, handler):
        """Called by the client when a user wants to start up a new application."""
        #save the perspective for later use
        #TODO: make sure perspective is removed when app is closed
        run = RunningApplication(perspective, handler)
        self.runningApplications[handler] = run
        #simply call the start method
        self.start(run)
    def view_shutdownApplication(self, perspective, handler):
        """Called by the client when a user wants to shutdown the application."""
        run =  self.runningApplications[handler]
        #simply call the shutdown method
        self.shutdown(run)
        del self.runningApplications[handler]
    def start(self, run):
        """Subclasses should start their applications here"""
        pass
    def shutdown(self, run):
        """Subclasses should put any shutdown code here"""
        pass
        
class PyropeWidget(pb.Referenceable):
    type = "PyropeWidget"
    def __init__(self, run):
        self.run = run
        run.widgets.append(self)
        #the remote reference will be set when the client supplies it
        self.remote = None
        #for event handling
        self.eventHandlers = {}
    @inlineCallbacks
    def createRemote(self):
        #creates remote widget, and gets a pb.RemoteReference to it's client-side proxy
        self.remote = yield self.run.handler.callRemote("createWidget", self.getConstructorDetails())
    def callRemote(self, functName, *args):
        if self.remote:
            return self.remote.callRemote(functName, *args)
        else:
            raise RemoteResourceNotCreatedException, "You must call createRemote before calling this method"
    def bind(self, event, handlerFunction):
        self.eventHandlers[event] = handlerFunction
    def remote_handleEvent(self, event):
        """Called by client when an event has been fired. """
        #update local cached data
        event.widget.handleEvent(event)
        #call event handler
        #TODO: support multiple handlers
        self.eventHandlers[event.eventType](event)
    def remote_updateRemote(self, remote):
        self.remote = remote

class Window(PyropeWidget):
    type = "Window"
    def __init__(self, run, parent, position=DefaultPosition, size=DefaultSize):
        PyropeWidget.__init__(self, run)
        self.parent = parent
        if parent != None:
            parent.children.append(self)
        self.pos = position
        self.size = size
        #other props
        self.children = []
    def getConstructorDetails(self):
        """Creates an instance of WidgetConstructorDetails, with all the details the client needs to create 
        the client-side version of this widget"""
        return WidgetConstructorDetails(self, self.type, self._getConstructorData(), self._getOtherData(), self._getStyleData(), 
                                        self._getChildren(), self._getEventHandlers())
    def _getConstructorData(self):
        d = {}
        d["parent"] = self.parent
        d["pos"] = self.pos
        d["size"] = self.size
        return d
    def _getOtherData(self):
        pass
    def _getStyleData(self):
        pass
    def _getEventHandlers(self):
        eventHandlers = []
        for event, fn in self.eventHandlers.items():
            eventHandlers.append(event)
        return eventHandlers
    def _getChildren(self):
        children = []
        for child in self.children:
            children.append(child.getConstructorDetails())
        return children
    def handleEvent(self, event):
        """Default response to an event is to ignore it. Implement useful behaviour in subsclasses (e.g. for TextBox, on a EventText, update the textboxes value attribute)"""
        pass
    def clientToScreen(self, point):
        return self.callRemote("ClientToScreen", point)
    def hide(self):
        return self.callRemote("Hide")
    def show(self):
        return self.callRemote("Show")
    def centre(self, direction=wx.BOTH, centreOnScreen=False):
        return self.callRemote("Centre", direction, centreOnScreen)
    def destroy(self):
        return self.callRemote("Destroy")
    def disable(self):
        return self.callRemote("Disable")
    def enable(self):
        return self.callRemote("Enable")

#    def GetBackgroundColour(self):
#        #simply return the background colour
#        return self._backgroundColour
#    def SetBackgroundColour(self, colour):
#        #set the local background colour
#        self._backgroundColour = colour
#        #set remote
#        return self.callRemote("SetBackgroundColour", colour)
#    #XXX: this doesn't work for setter!
#    backgroundColour = property(GetBackgroundColour, SetBackgroundColour)

#class BoxSizer(PyropeWidget):
#    def __init__(self, app, handler, orientation):
#        PyropeWidget.__init__(self, app, handler)
#        self.orientation = orientation
#        self.widgets = []
#    def add(self, widget):
#        self.widgets.append(widget)
#pb.setUnjellyableForClass(BoxSizer, BoxSizer)
#
#class Panel(Window):
#    def __init__(self, app, handler, parent, position=DefaultPosition, size=DefaultSize, style=wx.TAB_TRAVERSAL):
#        Window.__init__(self, app, handler, parent, position=position, size=size, style=style)
#pb.setUnjellyableForClass(Panel, Panel)

class TextBox(Window):
    type = "TextBox"
    def __init__(self, run, parent, value=u"", position=DefaultPosition, size=DefaultSize):
        Window.__init__(self, run, parent, position=position, size=size)
        self.value = value
    def _getConstructorData(self):
        d = Window._getConstructorData(self)
        d["value"] = self.value
        return d
    def handleEvent(self, event):
        #TODO: check the event type, handle accordingly, throw exceptions if it can't handle it
        self.value = event.data
class Label(Window):
    type = "Label"
    def __init__(self, run, parent, value=u"", position=DefaultPosition, size=DefaultSize):
        Window.__init__(self, run, parent, position=position, size=size)
        self.label = value
    def _getConstructorData(self):
        d = Window._getConstructorData(self)
        d["label"] = self.label
        return d
    def setValue(self, label):
        #set the local background colour
        self.label = label
        #set remote
        return self.callRemote("SetLabel", label)
    def handleEvent(self, event):
        self.label = event.data

######################
# Frames and Dialogs #
######################

#class Frame(Window):
#    type = "Frame"
#    def __init__(self, run, parent, title=u"", position=DefaultPosition, size=DefaultSize, style=wx.DEFAULT_FRAME_STYLE):
#        Window.__init__(self, run, parent, position=position, size=size, style=style)
#        self.title = title
#    def getConstructorData(self):
#        d = Window.getConstructorData(self)
#        d["title"] = self.title
#        return d
#
#class MiniFrame(Window):
#    type = "MiniFrame"
#    def __init__(self, run, parent, title=u"", position=DefaultPosition, size=DefaultSize, style=wx.DEFAULT_FRAME_STYLE):
#        Window.__init__(self, run, parent, position=position, size=size, style=style)
#        self.title = title
#    def getConstructorData(self):
#        d = Window.getConstructorData(self)
#        d["title"] = self.title
#        return d


class Frame(Window):
    """A Pyrope Frame uses a wxPython SizedFrame on the client-side. This is so, at least for simple cases, programmers won't
    need to deal with sizers so much."""
    type = "SizedFrame"
    def __init__(self, run, parent, title=u"", position=DefaultPosition, size=DefaultSize, sizerType="horizontal"):
        Window.__init__(self, run, parent, position=position, size=size)
        self.title = title
        self.sizerType = sizerType
    def _getConstructorData(self):
        d = Window._getConstructorData(self)
        d["title"] = self.title
        return d
    def _getOtherData(self):
        return {"sizerType":self.sizerType}

class Dialog(Window):
    type = "SizedDialog"
    def __init__(self, run, parent, title=u"", position=DefaultPosition, size=DefaultSize):
        Window.__init__(self, run, parent, position=position, size=size)
        self.title = title
    def _getConstructorData(self):
        d = Window._getConstructorData(self)
        d["title"] = self.title
        return d
    def showModal(self):
        return self.callRemote("ShowModal")
pb.setUnjellyableForClass(Dialog, Dialog)

class MessageDialog(Window):
    type = "MessageDialog"
    def __init__(self, run, parent, message, caption=u"Message Box", position=DefaultPosition):
        Window.__init__(self, run, parent, position=position)
        self.caption = caption
        self.message = message
    def _getConstructorData(self):
        d = Window._getConstructorData(self)
        d["caption"] = self.caption
        d["message"] = self.message
        #no size for message box
        del d["size"]
        return d
    def showModal(self):
        return self.callRemote("ShowModal")
pb.setUnjellyableForClass(MessageDialog, MessageDialog)

#########
# Panel #
#########
class Panel(Window):
    type = "SizedPanel"
    def __init__(self, run, parent, position=DefaultPosition, size=DefaultSize, sizerType="vertical"):
        Window.__init__(self, run, parent, position=position, size=size)
        self.sizerType = sizerType
    def _getOtherData(self):
        return {"sizerType":self.sizerType}

###########
# Widgets #
###########
class Button(Window):
    type = "Button"
    def __init__(self, run, parent, value=u""):
        Window.__init__(self, run, parent)
        self.label = value
    def _getConstructorData(self):
        d = Window._getConstructorData(self)
        d["label"] = self.label
        return d

class Choice(Window):
    type = "Choice"
    def __init__(self, run, parent, choices=u""):
        Window.__init__(self, run, parent)
        self.choices = choices
    def _getConstructorData(self):
        d = Window._getConstructorData(self)
        d["choices"] = self.choices
        return d

class CheckBox(Window):
    type = "CheckBox"
    def __init__(self, run, parent, label=u"", position=DefaultPosition, size=DefaultSize):
        Window.__init__(self, run, parent, position=position, size=size)
        self.label = label
    def _getConstructorData(self):
        d = Window._getConstructorData(self)
        d["label"] = self.label
        return d

class ThreeStateCheckBox(Window):
    type = "CheckBox"
    def __init__(self, run, parent, label=u"", position=DefaultPosition, size=DefaultSize):
        Window.__init__(self, run, parent, position=position, size=size)
        self.label = label
    def _getConstructorData(self):
        d = Window._getConstructorData(self)
        d["label"] = self.label
        return d

class Gauge(Window):
    type = "Gauge"
    def __init__(self, run, parent, range=100, position=DefaultPosition, size=DefaultSize):
        Window.__init__(self, run, parent, position=position, size=size)
        self.range = range
    def _getConstructorData(self):
        d = Window._getConstructorData(self)
        d["range"] = self.range
        return d
