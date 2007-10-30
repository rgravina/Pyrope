#Twisted imports
from twisted.cred import portal
from twisted.spread import pb
from twisted.application import internet
from twisted.application import service
from twisted.python import log
from zope.interface import Interface, Attribute, implements
#Pyrope imports
from pyrope.errors import *
    
class PyropeServer(pb.Root):
    def __init__(self):
        self._applications = []
    def remote_getApplications(self):
        return self._applications
    def registerApplication(self, app):
        if app in self._applications:
            raise ApplicationAlreadyRegisteredException, "Applcation %s already registered" % app
        self._applications.append(app)

class PyropeService(internet.TCPServer):
    """A Pyrope application server. After creating a PyropeServer instance, add your appication using 
    registerApplication and call startup."""
    def __init__(self, port=8789):
        ### startup server ###
        #listen for connections
        self._server = PyropeServer()
        internet.TCPServer.__init__(self, port, pb.PBServerFactory(self._server))
    
    def getServer(self):
        return self._server

    def startup(self):
        """ Starts listening for client connections """
        self.setServiceParent(application)

    def startService(self):
        log.msg("Pyrope server READY")

    def stopService(self):
        log.msg("Pyrope server SHUTTING DOWN")

application = service.Application("Pyrope")
service = PyropeService()
