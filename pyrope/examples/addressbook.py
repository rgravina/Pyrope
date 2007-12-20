import wx
from pyrope.server import Application
from pyrope.model import *

class AddressBookEntry:
    def __init__(self, name, email):
        self.name = name
        self.email = email
        
entries=[AddressBookEntry("Robert Gravina", "robert@gravina.com"), AddressBookEntry("Waka Inoue", "waka@inoue.com")]

class AddressBookFrame(Frame):
    def __init__(self, run, parent):
        Frame.__init__(self, run, parent, title=u"Address Book")

        #left panel - list of address book entries
        
        leftPanel = Panel(run, self)
        self.list = ListBox(run, leftPanel, choices=[entry.name for entry in entries], size=(150, 200))
        #select first entry
        self.list.selectedItem = 0
        self.list.bind(ListBoxEvent, self.onListBoxSelect)

        #right panel - address book entry form
        rightPanel = Panel(run, self, sizerType="form")
        Label(run, rightPanel, value=u"Name")
        self.name = TextBox(run, rightPanel, size=(170,-1))
        Label(run, rightPanel, value=u"Email")
        self.email = TextBox(run, rightPanel, size=(170,-1))

        self.statusBar = StatusBar(run, self)
        self.statusBar.fields = {0:u"%d entires" % len(entries)}

    def onListBoxSelect(self, event):
        def _done(result):
            index = self.list.selectedIndex
            self.name.value = entries[index].name 
            self.email.value = entries[index].email
            self.name.syncWithLocal()
            self.email.syncWithLocal()             
        self.list.syncWithRemote().addCallback(_done)

class AddressBookApplication(Application):
    def __init__(self):
        Application.__init__(self, "Address Book", description="A basic address book application.")

    def start(self, run):
        def _done(result):
            frame.centre()
            frame.show()
        frame = AddressBookFrame(run, None)
        frame.createRemote().addCallback(_done)
