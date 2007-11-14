from twisted.spread import pb
from twisted.python import log
from twisted.internet.defer import inlineCallbacks
#from twisted.spread.flavors import NoSuchMethod
from pyrope.model.shared import *

class RemoteApplication(pb.Copyable, pb.RemoteCopy):
    def __init__(self, app):
        self.name = app.name
        self.description = app.description
        self.server = app
pb.setUnjellyableForClass(RemoteApplication, RemoteApplication)

#class PyropeReferenceable(pb.Referenceable):
#    def remoteMessageReceived(self, broker, message, args, kw):
#        try:
#            return pb.Referenceable.remoteMessageReceived(self, broker, message, args, kw)
#        except NoSuchMethod:
#            return getattr(self.widget, message)()

class LocalWindowReference(pb.Referenceable):
    def __init__(self, app, widget, id, handlers):
        self.app = app
        self.widget = widget
        self.id = id
        self.boundEvents = []
        for event in handlers:
            self.boundEvents.append(events[event])
    def remote_show(self):
        return self.widget.Show()
    def remote_clientToScreen(self, point):
        point = self.widget.ClientToScreen(point)
        #can't return a wxPoint directly over the network, so return a tuple instead
        #TODO: generalise this
        return (point.x, point.y)

class LocalFrameReference(LocalWindowReference):
    def _destroy(self):
        self.app.topLevelWindows.remove(self.widget)
        if not self.app.topLevelWindows:
            self.app.shutdown()
        self.widget.Destroy()
    def onClose(self, event):
        if wx.EVT_CLOSE in self.boundEvents:
            self.app.app.server.callRemote("event", self.id, EventClose)
        else:
            self._destroy()
    def remote_centre(self, direction, centreOnScreen):
        dir = direction
        if centreOnScreen:
            dir | wx.CENTRE_ON_SCREEN
        return self.widget.Centre(direction = dir)

    def remote_destroy(self):
        self._destroy()

class RemoteApplicationHandler(pb.Referenceable):
    def __init__(self, app, appPresenter):
        self.app = app
        self.appPresenter = appPresenter
        #only for wx.Frame and wx.Dialogue
        self.topLevelWindows = []
    def remote_createWindow(self, remoteWindow):
        #create wxFrame
        window = wx.Window(None, wx.ID_ANY, size=remoteWindow.size, pos=remoteWindow.position, style=remoteWindow.style)
        localRef = LocalWindowReference(self, window, remoteWindow.id, remoteWindow.handlers)
        return self.app.server.callRemote("createdWindow", localRef, remoteWindow.id)
    def remote_createFrame(self, remoteFrame):
        #create wxFrame
        frame = wx.Frame(None, wx.ID_ANY, remoteFrame.title, size=remoteFrame.size, pos=remoteFrame.position, style=remoteFrame.style)
        localRef = LocalFrameReference(self, frame, remoteFrame.id, remoteFrame.handlers)
        self.app.server.callRemote("createdWindow", localRef, remoteFrame.id)
        frame.Bind(wx.EVT_CLOSE, localRef.onClose)
        self.topLevelWindows.append(frame)
    def shutdown(self):
        def _shutdown(result):
            self.appPresenter.runningApplications.remove(self.app)
        return self.app.server.callRemote("shutdownApplication", self).addCallback(_shutdown)

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
