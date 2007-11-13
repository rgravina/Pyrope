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
    def __init__(self, app, widget):
        self.app = app
        self.widget = widget
    def remote_show(self):
        return self.widget.Show()

class LocalFrameReference(LocalWindowReference):
    def onClose(self, event):
        self.app.topLevelWindows.remove(self.widget)
        if not self.app.topLevelWindows:
            self.app.shutdown()
        self.widget.Destroy()
    def remote_centre(self, direction, centreOnScreen):
        dir = direction
        if centreOnScreen:
            dir | wx.CENTRE_ON_SCREEN
        return self.widget.Centre(direction = dir)

class RemoteApplicationHandler(pb.Referenceable):
    def __init__(self, app, appPresenter):
        self.app = app
        self.appPresenter = appPresenter
        #only for wx.Frame and wx.Dialogue
        self.topLevelWindows = []
    def remote_createWindow(self, remoteWindow):
        #create wxFrame
        window = wx.Window(None, wx.ID_ANY, size=remoteWindow.size, pos=remoteWindow.position, style=remoteWindow.style)
        localRef = LocalWindowReference(self, window)
        return self.app.server.callRemote("createdWindow", localRef, remoteWindow.id)
    def remote_createFrame(self, remoteFrame):
        #create wxFrame
        frame = wx.Frame(None, wx.ID_ANY, remoteFrame.title, size=remoteFrame.size, pos=remoteFrame.position, style=remoteFrame.style)
        localRef = LocalFrameReference(self, frame)
        frame.Bind(wx.EVT_CLOSE, localRef.onClose)
        self.topLevelWindows.append(frame)
        return self.app.server.callRemote("createdWindow", localRef, remoteFrame.id)
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