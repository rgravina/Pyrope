from twisted.spread import pb

class AddressBookEntry(pb.Copyable, pb.RemoteCopy):
    def __init__(self, name, email):
        self.name = name
        self.email = email
pb.setUnjellyableForClass(AddressBookEntry, AddressBookEntry)
