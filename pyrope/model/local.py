from axiom.item import Item
from axiom.attributes import text
from zope.interface import implements, Interface, Attribute
from twisted.spread import pb

class IApplication(Interface):
    """A Pyrope application"""
    name = Attribute("Application name")
    description = Attribute("Application description")

class Application(pb.Copyable):
    implements(IApplication)
    def __init__(self, name, description=None):
        self.name = name
        self.description = description
class RemoteApplication(pb.RemoteCopy):
    pass
pb.setUnjellyableForClass(Application, RemoteApplication)

class User(Item):
    username = text()
    password = text()
