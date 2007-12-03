"""The Remote (i.e. usually client-side) model."""
import wx
import wxaddons.sized_controls as sc
from twisted.spread import pb
from twisted.python import log
from twisted.spread.flavors import NoSuchMethod
from pyrope.model.shared import *
from zope.interface import Interface, Attribute, implements

class RemoteApplication(pb.Copyable, pb.RemoteCopy):
    """Describes a Pyrope application, with a reference to the application handler (pb.Referenceable on the server, pb.RemoteReference on the client)"""
    def __init__(self, app):
        self.name = app.name
        self.description = app.description
        self.server = app
pb.setUnjellyableForClass(RemoteApplication, RemoteApplication)

class WidgetConstructorDetails(pb.Copyable, pb.RemoteCopy):
    """Describes a information needed by the client to create a local wxWidget which represents a server-side Pyrope widget. 
    It is a U{Parameter Object<http://www.refactoring.com/catalog/introduceParameterObject.html>}"""
    def __init__(self, pyropeWidget):
        self.remoteWidgetReference = pyropeWidget
        self.type = pyropeWidget.__class__.type
        self.constructorData = pyropeWidget.getConstructorData()
        self.otherData = pyropeWidget.getOtherData()
        self.children = pyropeWidget.getChildren()
        self.eventHandlers = pyropeWidget.getEventHandlers()
pb.setUnjellyableForClass(WidgetConstructorDetails, WidgetConstructorDetails)

class Event(pb.Copyable, pb.RemoteCopy):
    def __init__(self, widget, eventType, data):
        self.widget = widget
        self.eventType = eventType
        self.data = data
pb.setUnjellyableForClass(Event, Event)

class PyropeReferenceable(pb.Referenceable):
    """Subclasses pb.Referenceable so that it calls self.widget.somemethod when remote_somemethod connot be found.
    This makes it simpler to wrap methods on wxWidgets classes."""
    def remoteMessageReceived(self, broker, message, args, kw):
        """ Calls self.widget.somemethod when remote_somemethod connot be found"""
        try:
            return pb.Referenceable.remoteMessageReceived(self, broker, message, args, kw)
        except NoSuchMethod:
            return getattr(self.widget, message)()

class WindowReference(PyropeReferenceable):
    """Manages a local wxWindow"""
    def __init__(self, app, widget, remote, handlers):
        self.app = app           #RemoteApplicationHandler
        self.widget = widget     #wxWindow    
        self.remote = remote     #server-side Pyrope widget refernce  
        self.boundEvents = []    #bound Pyrope events, e.g. EventClose
        for event in handlers:
            self.boundEvents.append(event)
            self.widget.Bind(events[event], self.handleEvent)            
    def remote_Destroy(self):
        self._destroy()
    def _destroy(self):
        """Check to see if this is the last window open (for this app) and if so, call shutdown on the RemoteApplicationHandler instance.
        Finally, destroy the widget."""
        self.app.topLevelWindows.remove(self.widget)
        if not self.app.topLevelWindows:
            self.app.shutdown()
        self.widget.Destroy()
    def onClose(self, event):
        if EventClose in self.boundEvents:
#            self.remote.callRemote("handleEvent", EventClose)
            pass
        else:
            self._destroy()
    def handleEvent(self, event):
        if event.GetEventType() == wx.EVT_TEXT.typeId:
            eventData = Event(self.remote, EventText, self.widget.GetValue())
        self.remote.callRemote("handleEvent", eventData)
        
    def remote_Centre(self, direction, centreOnScreen): 
        dir = direction
        if centreOnScreen:
            dir | wx.CENTRE_ON_SCREEN
        return self.widget.Centre(direction = dir)
    def remote_ClientToScreen(self, point):
        point = self.widget.ClientToScreen(point)
        #can't return a wxPoint directly over the network, so return a tuple instead
        #TODO: generalise this
        return (point.x, point.y)
    def remote_SetBackgroundColour(self, colour):
        return self.widget.SetBackgroundColour(colour)

class FrameReference(WindowReference):
    pass

class SizedFrameReference(WindowReference):
    pass

class SizedPanelReference(WindowReference):
    pass

class DialogReference(WindowReference):
    pass

class TextBoxReference(WindowReference):
    pass

class ButtonReference(WindowReference):
    pass

class LabelReference(WindowReference):
    def remote_SetLabel(self, label):
        return self.widget.SetLabel(label)

class WidgetBuilder(object):
    def replaceParent(self, app, widgetData):
        parent = widgetData.constructorData["parent"]
        if parent:
            widget =  app.widgets[parent] 
            if isinstance(widget, sc.SizedFrame):
                widgetData.constructorData["parent"] = widget.GetContentsPane()
            else:
                widgetData.constructorData["parent"] = widget
                 
    def createLocalReference(self, app, widgetData):
        #XXX: this will break if called from a WidgetBuilder instance!
        window = self.widgetClass(**widgetData.constructorData)
        localRef = self.referenceClass(app, window, widgetData.remoteWidgetReference, widgetData.eventHandlers)
        app.widgets[widgetData.remoteWidgetReference] = localRef.widget
        return localRef

class FrameBuilder(WidgetBuilder):
    widgetClass = wx.Frame
    referenceClass = FrameReference
    def createLocalReference(self, app, widgetData):
        localRef = WidgetBuilder.createLocalReference(self, app, widgetData)
        localRef.widget.Bind(wx.EVT_CLOSE, localRef.onClose)
        app.topLevelWindows.append(localRef.widget)
        if widgetData.children:
            for childData in widgetData.children:
                childRef = WidgetFactory.create(app, childData)
                #server needs to know about child reference
                childData.remoteWidgetReference.callRemote("updateRemote", childRef)
        return localRef

class SizedFrameBuilder(FrameBuilder):
    widgetClass = sc.SizedFrame
    referenceClass = SizedFrameReference
    def createLocalReference(self, app, widgetData):
        localRef = FrameBuilder.createLocalReference(self, app, widgetData)
        panel = localRef.widget.GetContentsPane()
        panel.SetSizerType(widgetData.otherData["sizerType"])
        return localRef

class SizedPanelBuilder(FrameBuilder):
    widgetClass = sc.SizedPanel
    referenceClass = SizedPanelReference

class TextBoxBuilder(WidgetBuilder):
    widgetClass = wx.TextCtrl
    referenceClass = TextBoxReference

class LabelBuilder(WidgetBuilder):
    widgetClass = wx.StaticText
    referenceClass = LabelReference

class ButtonBuilder(WidgetBuilder):
    widgetClass = wx.Button
    referenceClass = ButtonReference

class WidgetFactory(object):
    """A Factory that produces wxWidgets based on the class of the remote Pyrope widget passed to the constructor."""
    @classmethod
    def create(cls, app, widgetData):
        builder = eval(widgetData.type+"Builder")()
        #if the remote widget has a parent (supplied as a pb.RemoteReference) replace the attribute with the coressponding wxWindow which is it's real parent
        builder.replaceParent(app, widgetData)
        #create and return the local pb.Referenceable that will manage this widget
        return builder.createLocalReference(app, widgetData)

class RemoteApplicationHandler(pb.Referenceable):
    def __init__(self, app, appPresenter):
        self.app = app
        self.appPresenter = appPresenter
        #only for wx.Frame and wx.Dialog
        self.topLevelWindows = []
        self.widgets = {}
    def shutdown(self):
        def _shutdown(result):
            self.appPresenter.shutdownApplication(self.app)
        return self.app.server.callRemote("shutdownApplication", self).addCallback(_shutdown)
    def remote_createWidget(self, widgetData):
        #create widget and local proxy
        #return pb.RemoteReference to server
        return WidgetFactory.create(self, widgetData)

class PyropeClientHandler(pb.Referenceable):
    pass
