from eskimoapps.ui.application import *
from eskimoapps.ui.databoundui import *
from twisted.spread import pb
from twisted.internet import reactor
from views import *
from interactors import *
from pyrope.model import *

class PyropeApplicationPresenter(ApplicationPresenter):
    def __init__(self, appName, reactor, host, port, redirect, username="anonymous", password="anonymous"):
        Presenter.__init__(self, ApplicationModel.getInstance(host, port, username, password)
                           , ApplicationView(appName, redirect=redirect)
                           , Interactor())
        WindowPresenterMixin.app = self
        #list of open windows (the Presenters of the windows, anyway) in the application
        self.openWindows = []
        #list of all running applications
        self.runningApplications = []
        #Twisteds reactor
        self._reactor = reactor        
        #is there an error?
        self.error = False
        #progress bar
        self.progress = None
        self.localHandler = PyropeClientHandler()

        self.applications = None
        self.presenterLogon = None

    def initView(self):
        self.presenterLogon = LogonPresenter(LogonView(None), LogonInteractor());

    def connect(self):
        factory = pb.PBClientFactory()
        reactor.connectTCP(self.model.host, self.model.port, factory)
        factory.login(self.model.credentials, client=self.localHandler).addCallback(self.onConnect)

    def onConnect(self, perspective):
        def _gotApplications(applications):
            self.applications = ListofObjectsModel(applications, ["name"])
            self._showOpenScreen()
            self.presenterLogon.view.Hide()
        ApplicationPresenter.onConnect(self, perspective)
        #now we have the persective, we can ask the server what applications are available
        self.callRemote("getApplications").addCallback(_gotApplications)
        
    def _showOpenScreen(self):
        view = SimpleOpenView(self.applications, "Applications on "+self.model.host, "Applications", openButtonText="Run")
        presenterOpen = OpenApplicationPresenter(self.applications, view, SimpleOpenInteractor())
        presenterOpen.start()
        
    def shutdownApplication(self, app):
        self.runningApplications.remove(app)
        if not self.runningApplications:
            self._showOpenScreen()

class LogonPresenter(Presenter, WindowPresenterMixin):
    def __init__(self, view, interactor):
        Presenter.__init__(self, None, view, interactor)
        WindowPresenterMixin.__init__(self)
        self.start()

    def onLoadViewFromModel(self):
        appmodel = PyropeApplicationPresenter.getInstance().model
        self.view.serverName = appmodel.host
        self.view.serverPort = appmodel.port

    def onUpdateModelFromView(self):
        appmodel = PyropeApplicationPresenter.getInstance().model
        appmodel.host = self.view.serverName
        appmodel.port = self.view.serverPort
        self.connect()      

    def enableConnect(self, enabled):
        self.view.btnConnect.Enable(enabled)

    def connect(self):
        PyropeApplicationPresenter.getInstance().connect()

    def onClose(self):
        WindowPresenterMixin.onClose(self)

class OpenApplicationPresenter(SimpleOpenPresenter):
    def onClose(self):
        SimpleOpenPresenter.onClose(self)
        PyropeApplicationPresenter.getInstance().presenterLogon.view.Show()
        
    def onOpen(self):
        #TODO: uncomment this when figured out how to know when last window of application is closed (not Pyrope, the running app)
        def _openedApplication(result, application):
            #application started. add to list of running applications
            PyropeApplicationPresenter.getInstance().runningApplications.append(application)
            SimpleOpenPresenter.onClose(self)
        #OK now we need to tell the server to start the application and wait for something to happen
        application = self.model.getObjectAt(self.view.lstObjects.getSelectedIndex())
        application.handler = RemoteApplicationHandler(application, PyropeApplicationPresenter.getInstance())
        application.server.callRemote("startApplication", application.handler).addCallback(_openedApplication, application)
