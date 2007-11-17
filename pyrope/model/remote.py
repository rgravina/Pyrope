import wx
from twisted.spread import pb
from twisted.python import log
from twisted.spread.flavors import NoSuchMethod
from pyrope.model.shared import *

class RemoteApplication(pb.Copyable, pb.RemoteCopy):
    """Describes a Pyrope application, with a reference to the application handler (pb.Referenceable on the server, pb.RemoteReference on the client"""
    def __init__(self, app):
        self.name = app.name
        self.description = app.description
        self.server = app
pb.setUnjellyableForClass(RemoteApplication, RemoteApplication)

class PyropeReferenceable(pb.Referenceable):
    """Subclasses pb.Referenceable so that it calles self.widget.somemethod when remote_somemethod connot be found.
    This makes it simpler to wrap methods on wxWidgets classes."""
    def remoteMessageReceived(self, broker, message, args, kw):
        try:
            return pb.Referenceable.remoteMessageReceived(self, broker, message, args, kw)
        except NoSuchMethod:
            return getattr(self.widget, message)()

class LocalWindowReference(PyropeReferenceable):
    """Manages a local wxWindow"""
    def __init__(self, app, widget, id, handlers):
        self.app = app
        self.widget = widget
        self.id = id
        self.boundEvents = []
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
            self.app.app.server.callRemote("handleEvent", self.id, EventClose)
        else:
            self._destroy()
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

class LocalFrameReference(LocalWindowReference):
    pass

class LocalDialogReference(LocalWindowReference):
    pass

class WidgetFactory(object):
    @classmethod
    def create(cls, app, remote):
        if remote.parent:
            parent = app.widgets[remote.parent]
        else: 
            parent = None
        widget, localRef = getattr(WidgetFactory, "create"+remote.__class__.__name__)(app, parent, remote)
        app.app.server.callRemote("updateWidgetRemoteReference", localRef, remote.id)
        return widget, localRef
    @classmethod
    def createWindow(cls, app, parent, remote):
        window = wx.Window(parent, wx.ID_ANY, size=remote.size, pos=remote.position, style=remote.style)
        localRef = LocalWindowReference(app, window, remote.id, remote.eventHandlers)
        return window, localRef
    @classmethod
    def createFrame(cls, app, parent, remote):
        frame = wx.Frame(parent, wx.ID_ANY, remote.title, size=remote.size, pos=remote.position, style=remote.style)
        localRef = LocalFrameReference(app, frame, remote.id, remote.eventHandlers)
        frame.Bind(wx.EVT_CLOSE, localRef.onClose)
        app.topLevelWindows.append(frame)
        return frame, localRef
    @classmethod
    def createDialog(cls, app, parent, remote):
        dialog = wx.Dialog(parent, wx.ID_ANY, remote.title, size=remote.size, pos=remote.position, style=remote.style)
        localRef = LocalDialogReference(app, dialog, remote.id, remote.eventHandlers)
        dialog.Bind(wx.EVT_CLOSE, localRef.onClose)
        self.topLevelWindows.append(dialog)
        return dialog, localRef
    @classmethod
    def createMessageDialog(cls, app, parent, remote):
        dialog = wx.MessageDialog(parent, remote.message, caption=remote.title, pos=remote.position, style=remote.style)
        localRef = LocalDialogReference(app, dialog, remote.id, remote.eventHandlers)
        dialog.Bind(wx.EVT_CLOSE, localRef.onClose)
        app.topLevelWindows.append(dialog)
        return dialog, localRef
    
class RemoteApplicationHandler(pb.Referenceable):
    def __init__(self, app, appPresenter):
        self.app = app
        self.appPresenter = appPresenter
        #only for wx.Frame and wx.Dialog
        self.topLevelWindows = []
        self.widgets = {}
    def shutdown(self):
        def _shutdown(result):
            self.appPresenter.runningApplications.remove(self.app)
        return self.app.server.callRemote("shutdownApplication", self).addCallback(_shutdown)
    def remote_createWidget(self, remoteWidget):
        widget, localRef = WidgetFactory.create(self, remoteWidget)
        self.widgets[remoteWidget.id] = widget

class PyropeClientHandler(pb.Referenceable):
    pass
#    def __init__(self):
#        self.widgets = {}
#    def remote_createFrame(self, remoteFrame):
#        #create wxFrame
#        frame = wx.Frame(None, wx.ID_ANY, remoteFrame.title)
#        #associate Pyrope Frame ID with wxWidget
#        self.widgets[remoteFrame.id] = frame    
#    def remote_show(self, id):
#        self.widgets[id].Show()
#    def remote_createPanel(self, remotePanel):
#        parent = self.widgets[remotePanel.parent]        
#        panel = wx.Panel(parent, wx.ID_ANY)
#        self.widgets[remotePanel.id] = panel
#    def remote_createButton(self, remoteButton):
#        parent = self.widgets[remoteButton.parent]        
#        button = wx.Button(parent, wx.ID_ANY, remoteButton.label)
#        self.widgets[remoteButton.id] = button
#    def remote_createNotebook(self, remoteNotebook):
#        parent = self.widgets[remoteNotebook.parent]
#        notebook = wx.Notebook(parent, wx.ID_ANY)
#        self.widgets[remoteNotebook.id] = notebook
#    def remote_addPage(self, notebookID, panelID, title):
#        notebook = self.widgets[notebookID]
#        panel = self.widgets[panelID]
#        notebook.AddPage(panel, title)
#    def remote_createBoxSizer(self, remoteSizer):
#        sizer = wx.BoxSizer()
#        self.widgets[remoteSizer.id] = sizer
