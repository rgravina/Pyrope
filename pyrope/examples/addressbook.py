import wx
from pyrope.server import Application
from pyrope.model import *

class AddressBookFrame(Frame):
    def __init__(self, run, parent):
        Frame.__init__(self, run, parent, title=u"Address Book")

        #left panel - list of address book entries
        leftPanel = Panel(run, self)
        ListBox(run, leftPanel, choices=[u"Robert Gravina"])

        #right panel - address book entry form
        rightPanel = Panel(run, self, sizerType="form")
        Label(run, rightPanel, value=u"Name")
        TextBox(run, rightPanel, value=u"Robert Gravina")
        Label(run, rightPanel, value=u"Email")
        TextBox(run, rightPanel, value=u"robert@gravina.com")

class AddressBookApplication(Application):
    def __init__(self):
        Application.__init__(self, "Address Book", description="A basic address book application.")

    def start(self, run):
        def _done(result):
            frame.centre()
            frame.show()
        frame = AddressBookFrame(run, None)
        frame.createRemote().addCallback(_done)
