from eskimoapps.ui.mvp import Presenter
from eskimoapps.ui.application import *
from eskimoapps.utils.singleton import Singleton
from pyrope.config import redirectStdout
from views import *

class PyropeApplicationPresenter(ApplicationPresenter):
    def initView(self):
        viewLogon = LogonView(None)
        presenterLogon = LogonPresenter(viewLogon, Interactor());
        viewLogon.start()

class LogonPresenter(Presenter, WindowPresenterMixin):
    """
    Presenter for the Logon screen. 
    """
    def __init__(self, view, interactor):
        Presenter.__init__(self, None, view, interactor)
        WindowPresenterMixin.__init__(self, PyropeApplicationPresenter.getInstance())
        self.progress = None
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

    def enableLogonAndCancel(self, enabled):
        self.view.btnLogon.Enable(enabled)
        self.view.btnCancel.Enable(enabled)

