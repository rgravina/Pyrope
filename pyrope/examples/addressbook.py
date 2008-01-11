import wx
from pyrope.server import Application
from pyrope.model import *
 
class AddressBookEntry:
    def __init__(self, name, email):
        self.name = name
        self.email = email
        
entries=[AddressBookEntry("Robert Gravina", "robert@gravina.com"), 
         AddressBookEntry("Guido van Rossum", "guido@python.org"),
         AddressBookEntry("Yukihiro Matsumoto", "yukihiro@ruby.org")]

class AddressBookFrame(Frame):
    def __init__(self, run, parent):
        Frame.__init__(self, run, parent, title=u"Address Book", sizerType="vertical")

        #left panel - list of address book entries
        listPanel = Panel(run, self, sizerType="horizontal")
        self.list = ListBox(run, listPanel, choices=[entry.name for entry in entries], size=(170, 180))
        self.list.bind(ListBoxEvent, self.onListBoxSelect)
        #right panel - address book entry form
        rightPanel = Panel(run, listPanel, sizerType="form")
        Label(run, rightPanel, value=u"Name")
        self.name = TextBox(run, rightPanel, size=(160,-1))
        Label(run, rightPanel, value=u"Email")
        self.email = TextBox(run, rightPanel, size=(160,-1))

        #buttons
        buttonPanel = Panel(run, self, sizerType="horizontal")
        self.addButton = Button(run, buttonPanel, value=u"+")
        self.addButton.bind(ButtonEvent, self.onAddButton)
        self.deleteButton = Button(run, buttonPanel, value=u"-")
        self.deleteButton.bind(ButtonEvent, self.onDeleteButton)
        self.saveButton = Button(run, buttonPanel, value=u"Save")
        self.saveButton.bind(ButtonEvent, self.onSave)
        
        self.statusBar = StatusBar(run, self, fields={0:u"%d entires" % len(entries)})

    def onListBoxSelect(self, event):
        index = event.data
        self.name.value = entries[index].name 
        self.email.value = entries[index].email

    def onSave(self, event):
        index = self.list.selectedIndex
        entries[index].name = self.name.value
        entries[index].email = self.email.value
        self.list.setChoice(index, self.name.value)
        
    def onAddButton(self, event):
        entries.append(AddressBookEntry("", ""))
        self.list.append("")
        self.list.selectedIndex = len(entries)-1
        self.clearControls()
        
    def onDeleteButton(self, event):
        index = self.list.selectedIndex
        del entries[index]
        self.list.delete(index)
        self.clearControls()

    def clearControls(self):
        self.name.value = ""
        self.email.value = ""

class AddressBookApplication(Application):
    def __init__(self):
        Application.__init__(self, "Address Book", description="A basic address book application.")

    def start(self, run):
        def _done(result):
            frame.centre()
            frame.show()
        frame = AddressBookFrame(run, None)
        frame.createRemote().addCallback(_done)
