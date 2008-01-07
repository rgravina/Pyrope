import wx
from pyrope.server import Application
from pyrope.model import *
 
class AddressBookEntry:
    def __init__(self, name, email):
        self.name = name
        self.email = email
        
entries=[AddressBookEntry("Robert Gravina", "robert@gravina.com"), 
         AddressBookEntry("Waka Inoue", "waka@inoue.com"),
         AddressBookEntry("Misaki Ito", "misaki@ito.com")]

class AddressBookFrame(Frame):
    def __init__(self, run, parent):
        Frame.__init__(self, run, parent, title=u"Address Book")

        #left panel - list of address book entries
        
        leftPanel = Panel(run, self)
        listPanel = Panel(run, leftPanel)
        self.list = ListBox(run, listPanel, choices=[entry.name for entry in entries], size=(150, 180))
        #select first entry
        self.list.selectedItem = 0
        self.list.bind(ListBoxEvent, self.onListBoxSelect)
        
        buttonPanel = Panel(run, listPanel, sizerType="horizontal")
        self.addButton = Button(run, buttonPanel, value=u"+")
        self.deleteButton = Button(run, buttonPanel, value=u"-")

        #right panel - address book entry form
        rightPanel = Panel(run, self, sizerType="form")
        Label(run, rightPanel, value=u"Name")
        self.name = TextBox(run, rightPanel, size=(170,-1))
        Label(run, rightPanel, value=u"Email")
        self.email = TextBox(run, rightPanel, size=(170,-1))

        #buttons
        self.saveButton = Button(run, rightPanel, value=u"Save")
        self.saveButton.bind(ButtonEvent, self.onSave)
        
        self.statusBar = StatusBar(run, self)
        self.statusBar.fields = {0:u"%d entires" % len(entries)}

    def onListBoxSelect(self, event):
        index = event.data
        self.name.value = entries[index].name 
        self.email.value = entries[index].email
        syncWithLocal(self.name, self.email)

    def onSave(self, event):
        def _done(result):
            index = self.list.selectedIndex
            entries[index].name = self.name.value
            entries[index].email = self.email.value
            self.list.choices = [entry.name for entry in entries]
            self.list.syncWithLocal()
        syncWithRemote(self.list, self.name, self.email).addCallback(_done)
        
class AddressBookApplication(Application):
    def __init__(self):
        Application.__init__(self, "Address Book", description="A basic address book application.")

    def start(self, run):
        def _done(result):
            frame.centre()
            frame.show()
        frame = AddressBookFrame(run, None)
        frame.createRemote().addCallback(_done)
