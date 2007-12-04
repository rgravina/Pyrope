import wx
from pyrope.server import Application
from pyrope.model import *

class AddressBookFrame(SizedFrame):
    def __init__(self, run, parent):
        SizedFrame.__init__(self, run, parent, title=u"Address Book", size=(500,400), style=wx.DEFAULT_FRAME_STYLE ^ wx.MAXIMIZE_BOX)
        leftPanel = SizedPanel(run, self)
        rightPanel = SizedPanel(run, self)

class AddressBookApplication(Application):
    def __init__(self):
        Application.__init__(self, "Address Book", description="A basic address book application.")

    def start(self, run):
        def _done(result):
            frame.Centre()
            frame.Show()

        frame = AddressBookFrame(run, None)
        frame.createRemote().addCallback(_done)
