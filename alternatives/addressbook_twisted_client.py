from twisted.internet import wxreactor
wxreactor.install()
import wx
from twisted.internet import reactor
from twisted.spread import pb
from addressbook_wxpython import AddressBookFrame
from addressbook_twisted_model import *

class TwistedAddressBookFrame(AddressBookFrame):
    def onSave(self, event):
        def _saved(result):
            self.list.SetString(index, self.entries[index].name)
        index = self.list.GetSelection()
        self.entries[index].name = self.name.GetValue()
        self.entries[index].email = self.email.GetValue()
        self.entries[index].phone = self.phone.GetValue()
        self.entries[index].address = self.address.GetValue()
        self.remote.callRemote("save", index, self.entries[index]).addCallback(_saved)

    def onAddButton(self, event):
        def _added(result):
            self.entries.append(AddressBookEntry("", ""))
            self.list.Append("")
            self.list.Select(len(self.entries)-1)
            self.clearControls()
        self.remote.callRemote("add").addCallback(_added)
    
    def onDeleteButton(self, event):
        def _deleted(result):
            del self.entries[index]
            self.list.Delete(index)
            self.clearControls()
        index = self.list.GetSelection()
        self.remote.callRemote("delete", index).addCallback(_deleted)

class AddressBookApplication:
    def __init__(self):
        self.addressBook = TwistedAddressBookFrame(None, [])

    def connected(self, remote):
        self.addressBook.remote = remote
        remote.callRemote("getEntries").addCallback(self.gotEntries)
    
    def gotEntries(self, entries):
        self.addressBook.entries = entries
        self.addressBook.list.Set([entry.name for entry in entries])
        self.addressBook.statusBar.SetStatusText("%d entries" % len(entries), 0)
        self.addressBook.statusBar.Refresh()
        
def main():
    #register the app
    app = wx.PySimpleApp()
    reactor.registerWxApp(app)

    #create the application and client
    addressBookApp = AddressBookApplication()
    factory = pb.PBClientFactory()
    reactor.connectTCP("localhost", 8800, factory)
    factory.getRootObject().addCallback(addressBookApp.connected)
    
    #start reactor
    reactor.run(True)

if __name__ == '__main__':
    main()