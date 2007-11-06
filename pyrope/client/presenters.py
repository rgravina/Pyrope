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
        #Twisteds reactor
        self._reactor = reactor        
        #is there an error?
        self.error = False
        #progress bar
        self.progress = None
        self.localHandler = LocalHandler()
        
    def initView(self):
        self.presenterLogon = LogonPresenter(LogonView(None), LogonInteractor());

    def connect(self):
        factory = pb.PBClientFactory()
        reactor.connectTCP(self.model.host, self.model.port, factory)
        factory.login(self.model.credentials, client=self.localHandler).addCallback(self.onConnect)

    def onConnect(self, perspective):
        def _gotApplications(applications):
            model = ListofObjectsModel(applications, ["name"])
            view = SimpleOpenView(model, "Start Application", "Applications")
            presenter = OpenApplicationPresenter(model, view, SimpleOpenInteractor())
            self.presenterLogon.onClose()
        ApplicationPresenter.onConnect(self, perspective)
        #now we have the persective, we can ask the server what applications are available
        self.callRemote("getApplications").addCallback(_gotApplications)
        
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

class OpenApplicationPresenter(SimpleOpenPresenter):        
    def onOpen(self):
        #OK now we need to tell the server to start the application and wait for something to happen
        application = self.model.getObjectAt(self.view.lstObjects.getSelectedIndex())
        application.server.callRemote("startApplication")
