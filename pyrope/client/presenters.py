from eskimoapps.ui.application import *
from views import *
from interactors import *

class PyropeApplicationPresenter(ApplicationPresenter):
    def __init__(self, appName, reactor, host, port, username="", password=""):
        Presenter.__init__(self, ApplicationModel.getInstance(host, port, username, password)
                           , PipelineApplicationView(appName, redirect=False)
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
        
    def initView(self):
        presenterLogon = LogonPresenter(LogonView(None), LogonInteractor());

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
        pass
