from twisted.application import service, internet
from twisted.internet import reactor
from twisted.spread import pb
from addressbook_twisted_model import *

entries=[]
for i in range(2):
    entries.extend((AddressBookEntry("Robert Gravina", "robert@gravina.com", 
                          "090 1234 5678", 
                          "123 Sample St.\nSample City\nSample Country"), 
         AddressBookEntry("Guido van Rossum", "guido@python.org", 
                          "090 1234 5678", 
                          "123 Sample St.\nSample City\nSample Country"),
         AddressBookEntry("Yukihiro Matsumoto", "yukihiro@ruby.org", 
                          "090 1234 5678", 
                          "123 Sample St.\nSample City\nSample Country"),
          AddressBookEntry("Yukihiro Matsumoto", "yukihiro@ruby.org", 
                          "090 1234 5678", 
                          "123 Sample St.\nSample City\nSample Country"),
         AddressBookEntry("Yukihiro Matsumoto", "yukihiro@ruby.org", 
                          "090 1234 5678", 
                          "123 Sample St.\nSample City\nSample Country")))
    
class AddressBookApplication(pb.Root):
    def remote_getEntries(self):
        return entries

    def remote_save(self, index, entry):
        entries[index] = entry

    def remote_add(self):
        entries.append(AddressBookEntry())

    def remote_delete(self, index):
        del entries[index]

application = service.Application("Address Book")
internet.TCPServer(8789, pb.PBServerFactory(AddressBookApplication())).setServiceParent(service.IServiceCollection(application))