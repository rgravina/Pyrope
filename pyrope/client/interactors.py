import wx
from eskimoapps.ui.mvp import Interactor

class LogonInteractor(Interactor):
    def Install(self, presenter, view):
        Interactor.Install(self, presenter, view)
        view.Bind(wx.EVT_CLOSE, self.onClose)
        view.btnConnect.Bind(wx.EVT_BUTTON, self.onConnect)
        view.btnCancel.Bind(wx.EVT_BUTTON, self.onCancel)

    def onConnect(self, evt):
        self.presenter.updateModelFromView()

    def onClose(self, evt):
        self.presenter.onClose()

    def onCancel(self, evt):
        self.presenter.onCancel()
