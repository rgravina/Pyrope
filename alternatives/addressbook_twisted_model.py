from twisted.spread import pb

class AddressBookEntry(pb.Copyable, pb.RemoteCopy):
    def __init__(self, name="", email="", phone="", address=""):
        self.name = name
        self.email = email
        self.phone = phone
        self.address = address
pb.setUnjellyableForClass(AddressBookEntry, AddressBookEntry)
