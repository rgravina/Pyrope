import wx
from mvp import View
import utils
from pyrope.config import *

class ApplicationView(wx.App, View):
    def OnInit(self):
        #setup wxApp instance
        wx.GetApp().SetAppName("Pyrope")    
        wx.SystemOptions.SetOptionInt("mac.window-plain-transition", 1)
        return True
    
    def displayError(self, title=u"Error", msg=u""):
        dlg = wx.MessageDialog(None, msg, title, wx.OK | wx.ICON_ERROR)
        dlg.ShowModal()
        dlg.Destroy()
        
    def displayMessage(self, title, msg):
        dlg = wx.MessageDialog(None, msg, title, wx.OK | wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

class LogonView(wx.Frame, View):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, title="Welcome to Pyrope!", size=(250, 280), style=wx.DEFAULT_FRAME_STYLE ^ (wx.RESIZE_BORDER|wx.MAXIMIZE_BOX))
        self.SetBackgroundColour(wx.Colour(255,255,255))

        labelSize = size=(70, -1)
        textSize = size=(150, -1)
        font = wx.SystemSettings.GetFont(wx.SYS_DEFAULT_GUI_FONT)
        
        boxServerName = wx.BoxSizer(wx.HORIZONTAL)
        boxServerName.Add(wx.StaticText(self, label="Server:", size=labelSize), 0, wx.ALIGN_RIGHT|wx.ALL, 5)
        self.txtServerName = wx.TextCtrl(self, size=textSize)
        boxServerName.Add(self.txtServerName, 1, wx.ALIGN_LEFT|wx.ALL, 5)
        boxServerPort = wx.BoxSizer(wx.HORIZONTAL)
        boxServerPort.Add(wx.StaticText(self, label="Port:", size=labelSize), 0, wx.ALIGN_RIGHT|wx.ALL, 5)
        self.txtServerPort = wx.TextCtrl(self, size=textSize)
        boxServerPort.Add(self.txtServerPort, 1, wx.ALIGN_LEFT|wx.ALL, 5)
        
        boxButtons = wx.BoxSizer(wx.HORIZONTAL)
        self.btnLogon = wx.Button(self, wx.ID_OK, "Connect")
        self.btnLogon.SetDefault()
        self.btnCancel = wx.Button(self, wx.ID_CANCEL, "Cancel")
        boxButtons.Add(self.btnCancel, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        boxButtons.Add(self.btnLogon, 0, wx.ALIGN_CENTRE|wx.ALL, 5)

        sizerMain = wx.BoxSizer(wx.VERTICAL)
        topImage = wx.Image(utils.opj("images/pyrope.png"), wx.BITMAP_TYPE_PNG).ConvertToBitmap()
        wx.StaticBitmap(self, -1, topImage, (0, 0), (topImage.GetWidth(), topImage.GetHeight()))
        sizerMain.Add((-1,topImage.GetHeight()+25))
        sizerBottom = wx.BoxSizer(wx.HORIZONTAL)
        sizerRight = wx.BoxSizer(wx.VERTICAL)
        sizerRight.Add(boxServerName)
        sizerRight.Add(boxServerPort)
        sizerBottom.Add(sizerRight,  wx.ALIGN_RIGHT|wx.RIGHT, 50)
        sizerMain.Add(sizerBottom)
        sizerMain.Add((-1, 25))
        sizerMain.Add(boxButtons, 0, wx.ALIGN_RIGHT|wx.RIGHT, 20)
        sizerMain.Add((-1, 5))
        lblCopyright = wx.StaticText(self, label="Version "+VERSION+"\n"+COPYRIGHT)
        lblCopyright.SetFont(font)
        sizerMain.Add(lblCopyright, 0, wx.ALIGN_CENTRE)
        self.SetSizer(sizerMain)
