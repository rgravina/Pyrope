from twisted.application import service, internet
from twisted.internet import reactor
from twisted.spread import pb
from addressbook_twisted_model import *

entries=[AddressBookEntry("Robert Gravina", "robert@gravina.com"), 
         AddressBookEntry("Guido van Rossum", "guido@python.org"),
         AddressBookEntry("Yukihiro Matsumoto", "yukihiro@ruby.org")]
    
class AddressBookApplication(pb.Root):
    def remote_getEntries(self):
        return entries

    def remote_save(self, index, entry):
        entries[index] = entry

    def remote_add(self):
        entries.append(AddressBookEntry("", ""))

    def remote_delete(self, index):
        del entries[index]

application = service.Application("Address Book")
internet.TCPServer(8800, pb.PBServerFactory(AddressBookApplication())).setServiceParent(service.IServiceCollection(application))