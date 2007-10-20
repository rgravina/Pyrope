from pyrope.singletonmixin import Singleton
from pyrope.config import redirectStdout
from mvp import Presenter, Interactor
from views import *
from models import ApplicationModel

class ApplicationPresenter(Singleton, Presenter):
    def __init__(self, host, port, username="admin", password="admin"):
        Presenter.__init__(self, ApplicationModel.getInstance(host, port, username, password)
                           , ApplicationView(redirect=redirectStdout)
                           , Interactor())
        
    def initView(self):
        #show logon screen
        viewLogon = LogonView(None)
#        presenterLogon = LogonPresenter(viewLogon, LogonInteractor());
        viewLogon.start()