from eskimoapps.ui.application import *
from views import *
from interactors import *

class PyropeApplicationPresenter(ApplicationPresenter):
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
