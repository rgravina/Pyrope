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
            self.remote.callRemote("handleEvent", EventClose)
        else:
            self._destroy()
    def handleEvent(self, event):
#        if event.GetEventType() == wx.EVT_TEXT.typeId:
#            eventType = EventText
#            data = self.widget.GetValue()
        self.remote.callRemote("handleEvent", eventType)
        
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

#class LocalSizerReference(PyropeReferenceable):
#    """Manages a local wxSizer"""
#    def __init__(self, app, widget, id):
#        self.app = app
#        self.widget = widget
#        self.id = id

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

#class SizerFactory(object):
#    @classmethod
#    def create(cls, app, remote):
#        localRef = getattr(SizerFactory, "create"+remote.__class__.__name__)(app, remote)
#        return localRef
#    @classmethod
#    def createBoxSizer(cls, app, remote):
#        sizer = wx.BoxSizer(remote.orientation)
#        localRef = LocalSizerReference(app, sizer, remote.id)
#        for widget in remote.widgets:
#            subref = WidgetFactory.create(app, widget)
#            app.app.server.callRemote("updateRemote", widget.id, subref)
#            sizer.Add(subref.widget)
#        return localRef

class WidgetBuilder(object):
    def replaceParent(self, app, widgetData):
        if widgetData.constructorData["parent"]:
            widgetData.constructorData["parent"] = app.widgets[widgetData.constructorData["parent"]]
        
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
    def replaceParent(self, app, widgetData):
        WidgetBuilder.replaceParent(self, app, widgetData)
        #XXX: assumes parent is a SizedFrame
        widgetData.constructorData["parent"] = widgetData.constructorData["parent"].GetContentsPane()

class TextBoxBuilder(WidgetBuilder):
    widgetClass = wx.TextCtrl
    referenceClass = TextBoxReference
    def replaceParent(self, app, widgetData):
        WidgetBuilder.replaceParent(self, app, widgetData)
        #XXX: assumes parent is a SizedFrame
        widgetData.constructorData["parent"] = widgetData.constructorData["parent"].GetContentsPane()

class LabelBuilder(WidgetBuilder):
    widgetClass = wx.StaticText
    referenceClass = LabelReference
    def replaceParent(self, app, widgetData):
        WidgetBuilder.replaceParent(self, app, widgetData)
        #XXX: assumes parent is a SizedFrame
        widgetData.constructorData["parent"] = widgetData.constructorData["parent"].GetContentsPane()

class ButtonBuilder(WidgetBuilder):
    widgetClass = wx.Button
    referenceClass = ButtonReference
    def replaceParent(self, app, widgetData):
        WidgetBuilder.replaceParent(self, app, widgetData)
        #XXX: assumes parent is a SizedFrame
        widgetData.constructorData["parent"] = widgetData.constructorData["parent"].GetContentsPane()

class WidgetFactory(object):
    """A Factory that produces wxWidgets based on the class of the remote Pyrope widget passed to the constructor."""
    @classmethod
    def create(cls, app, widgetData):
        builder = eval(widgetData.type+"Builder")()
        #if the remote widget has a parent (supplied as a pb.RemoteReference) get the coressponding wxWindow which is it's parent
        builder.replaceParent(app, widgetData)
        return builder.createLocalReference(app, widgetData)
#        localRef = getattr(WidgetFactory, "create"+widgetData.type)(app, widgetData)
#        #store in widgets dict, because child widgets might need it
#        app.widgets[widgetData.remoteWidgetReference] = localRef.widget
#        if widgetData.children:
#            for childData in widgetData.children:
#                childRef = WidgetFactory.create(app, childData)                
#        if remote.sizer:
#            try:
#                widget.SetSizer(app.widgets[remote.sizer.id])
#            except KeyError:
#                sizer, lr = SizerFactory.createBoxSizer(app, remote.sizer)
#                widget.SetSizer(sizer)
#        return localRef
#    @classmethod
#    def createWindow(cls, app, widgetData):
#        window = wx.Window(**widgetData.constructorData)
#        localRef = WindowReference(app, window, widgetData.remoteWidgetReference, widgetData.eventHandlers)
#        return localRef
#    @classmethod
#    def createFrame(cls, app, widgetData):
##        frame = wx.Frame(**widgetData.constructorData)
##        localRef = FrameReference(app, frame, widgetData.remoteWidgetReference, widgetData.eventHandlers)
#        frame.Bind(wx.EVT_CLOSE, localRef.onClose)
#        app.topLevelWindows.append(frame)
#        return localRef
#    @classmethod
#    def createSizedFrame(cls, app, widgetData):
#        frame = sc.SizedFrame(**widgetData.constructorData)
#        panel = frame.GetContentsPane()
#        panel.SetSizerType(widgetData.otherData["sizerType"])
#        localRef = SizedFrameReference(app, frame, widgetData.remoteWidgetReference, widgetData.eventHandlers)
#        frame.Bind(wx.EVT_CLOSE, localRef.onClose)
#        app.topLevelWindows.append(frame)
#        return localRef
#    @classmethod
#    def createSizedPanel(cls, app, widgetData):
#        widgetData.constructorData["parent"] = widgetData.constructorData["parent"].GetContentsPane()
#        panel = sc.SizedPanel(**widgetData.constructorData)
#        localRef = SizedPanelReference(app, panel, widgetData.remoteWidgetReference, widgetData.eventHandlers)
#        return localRef
#    @classmethod
#    def createDialog(cls, app, widgetData):
#        dialog = wx.Dialog(**widgetData.constructorData)
#        localRef = DialogReference(app, dialog, widgetData.remoteWidgetReference, widgetData.eventHandlers)
#        dialog.Bind(wx.EVT_CLOSE, localRef.onClose)
#        self.topLevelWindows.append(dialog)
#        return localRef
#    @classmethod
#    def createMessageDialog(cls, app, widgetData):
#        dialog = wx.MessageDialog(**widgetData.constructorData)
#        localRef = DialogReference(app, dialog, widgetData.remoteWidgetReference, widgetData.eventHandlers)
#        dialog.Bind(wx.EVT_CLOSE, localRef.onClose)
#        app.topLevelWindows.append(dialog)
#        return localRef
#    @classmethod
#    def createTextBox(cls, app, widgetData):
#        widgetData.constructorData["parent"] = widgetData.constructorData["parent"].GetContentsPane()
#        widget = wx.TextCtrl(**widgetData.constructorData)
#        localRef = TextBoxReference(app, widget, widgetData.remoteWidgetReference, widgetData.eventHandlers)
#        for event in  widgetData.eventHandlers:
#            widget.Bind(events[event], localRef.handleEvent)
#        return localRef
#    @classmethod
#    def createLabel(cls, app, widgetData):
#        widgetData.constructorData["parent"] = widgetData.constructorData["parent"].GetContentsPane()
#        widget = wx.StaticText(**widgetData.constructorData)
#        localRef = LabelReference(app, widget, widgetData.remoteWidgetReference, widgetData.eventHandlers)
#        return localRef
#    @classmethod
#    def createButton(cls, app, widgetData):
#        widgetData.constructorData["parent"] = widgetData.constructorData["parent"].GetContentsPane()
#        widget = wx.Button(**widgetData.constructorData)
#        localRef = ButtonReference(app, widget, widgetData.remoteWidgetReference, widgetData.eventHandlers)
#        return localRef

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
