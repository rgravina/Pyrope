"""The Remote (i.e. usually client-side) model."""
import wx
import wxaddons.sized_controls as sc
from twisted.spread import pb
from twisted.python import log
from twisted.spread.flavors import NoSuchMethod
from pyrope.model.shared import *

class RemoteApplication(pb.Copyable, pb.RemoteCopy):
    """Describes a Pyrope application, with a reference to the application handler (pb.Referenceable on the server, pb.RemoteReference on the client)"""
    def __init__(self, app):
        self.name = app.name
        self.description = app.description
        self.server = app
pb.setUnjellyableForClass(RemoteApplication, RemoteApplication)

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
        self.remote = remote             #server-side Pyrope widget refernce  
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

class WidgetFactory(object):
    """A Factory that produces wxWidgets based on the class of the remote Pyrope widget passed to the constructor."""
    @classmethod
    def create(cls, app, remote, data):
        #if the remote widget has a parent (supplied as an ID) get the coressponding wxWindow which is it's parent
        if data["parent"]:
            parent = app.widgets[data["parent"]]
        else: 
            parent = None
        localRef = getattr(WidgetFactory, "create"+data["type"])(app, parent, remote, data)
        #store in widgets dict, because child widgets might need it
        app.widgets[remote] = localRef.widget
#        if remote.children:
#            for child in remote.children:
#                childRef = WidgetFactory.create(app, child)
#                app.app.server.callRemote("updateRemote", child.id, app, childRef)
                
#        if remote.sizer:
#            try:
#                widget.SetSizer(app.widgets[remote.sizer.id])
#            except KeyError:
#                sizer, lr = SizerFactory.createBoxSizer(app, remote.sizer)
#                widget.SetSizer(sizer)
        return localRef
#    @classmethod
#    def createWindow(cls, app, parent, remote):
#        window = wx.Window(parent, wx.ID_ANY, size=remote.size, pos=remote.position, style=remote.style)
#        localRef = WindowReference(app, window, remote.id, remote.eventHandlers)
#        return localRef
    @classmethod
    def createFrame(cls, app, parent, remote, data):
        frame = wx.Frame(parent, wx.ID_ANY, data["title"], size=data["size"], pos=data["position"], style=data["style"])
        localRef = FrameReference(app, frame, remote, data["eventHandlers"])
        frame.Bind(wx.EVT_CLOSE, localRef.onClose)
        app.topLevelWindows.append(frame)
        return localRef
    @classmethod
    def createSizedFrame(cls, app, parent, remote, data):
        frame = sc.SizedFrame(parent, wx.ID_ANY, data["title"], size=data["size"], pos=data["position"], style=data["style"])
        panel = frame.GetContentsPane()
        panel.SetSizerType(data["sizerType"])
        localRef = SizedFrameReference(app, frame, remote, data["eventHandlers"])
        frame.Bind(wx.EVT_CLOSE, localRef.onClose)
        app.topLevelWindows.append(frame)
        return localRef
#    @classmethod
#    def createSizedPanel(cls, app, parent, remote):
#        parentPanel = parent.GetContentsPane()
#        panel = sc.SizedPanel(parentPanel, wx.ID_ANY, size=remote.size, pos=remote.position, style=remote.style)
#        localRef = SizedPanelReference(app, panel, remote.id, remote.eventHandlers)
#        return localRef
#    @classmethod
#    def createDialog(cls, app, parent, remote):
#        dialog = wx.Dialog(parent, wx.ID_ANY, remote.title, size=remote.size, pos=remote.position, style=remote.style)
#        localRef = DialogReference(app, dialog, remote.id, remote.eventHandlers)
#        dialog.Bind(wx.EVT_CLOSE, localRef.onClose)
#        self.topLevelWindows.append(dialog)
#        return localRef
#    @classmethod
#    def createMessageDialog(cls, app, parent, remote):
#        dialog = wx.MessageDialog(parent, remote.message, caption=remote.title, pos=remote.position, style=remote.style)
#        localRef = DialogReference(app, dialog, remote.id, remote.eventHandlers)
#        dialog.Bind(wx.EVT_CLOSE, localRef.onClose)
#        app.topLevelWindows.append(dialog)
#        return localRef
#    @classmethod
#    def createTextBox(cls, app, parent, remote):
#        panel = parent.GetContentsPane()
#        widget = wx.TextCtrl(panel, wx.ID_ANY, value=remote.value, size=remote.size, pos=remote.position, style=remote.style)
#        localRef = TextBoxReference(app, widget, remote.id, remote.eventHandlers)
#        for event in remote.eventHandlers:
#            widget.Bind(events[event], localRef.handleEvent)
#        return localRef
#    @classmethod
#    def createLabel(cls, app, parent, remote):
#        panel = parent.GetContentsPane()
#        widget = wx.StaticText(panel, wx.ID_ANY, label=remote.value, size=remote.size, pos=remote.position, style=remote.style)
#        localRef = LabelReference(app, widget, remote.id, remote.eventHandlers)
#        return localRef
#    @classmethod
#    def createButton(cls, app, parent, remote):
#        panel = parent.GetContentsPane()
#        widget = wx.Button(panel, wx.ID_ANY, label=remote.value, size=remote.size, pos=remote.position, style=remote.style)
#        localRef = ButtonReference(app, widget, remote.id, remote.eventHandlers)
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
    def remote_createWidget(self, remoteWidget, data):
        #create widget and local proxy
        #return pb.RemoteReference to server
        return  WidgetFactory.create(self, remoteWidget, data)

class PyropeClientHandler(pb.Referenceable):
    pass

