"""
The server component of Pyrope. 
Users should import application and service from this package (required to be defined if run by twistd), and create a server like so:

>>> from pyrope.server import application, service 
#add your application(s) here. e.g.
#service.registerApplication(HelloWorldApplication())
service.startup()

This can be run from a script e.g. twistd -ny demo.py. It will listen for connections from Pyrope clients (default port defined in pyrope/config.py)
"""
#Twisted imports
from twisted.cred import portal, checkers
from twisted.spread import pb
from twisted.application import internet
from twisted.application import service
from twisted.python import log
from zope.interface import implements
#Pyrope imports
from pyrope.errors import *
from pyrope.model import *
from pyrope.config import PORT

class PyropeRealm:
    """Pyrope realm accepts anonymous connnections from Pyrope clients. 
    We want this so users connecting to the server can get a list of applications and also so authentication can be dealt with on a per-application basis.
    TODO: provide a way to do this!"""
    implements(portal.IRealm)
    def requestAvatar(self, avatarID, mind, *interfaces):
        assert pb.IPerspective in interfaces
        avatar = AnonymousUserPerspective()
        avatar.server = self.server
        avatar.attached(mind)
        return pb.IPerspective, avatar, lambda a=avatar:a.detached(mind)

class AnonymousUserPerspective(pb.Avatar):
    """Represents an anonymous user connection"""
    #TODO: authentication on a per-application basis
    def attached(self, mind):
        """sets L{remote} = mind"""
        self.remote = mind
        log.msg("Anonymous user logged on")
    def detached(self, mind):
        """sets L{remote} = None"""
        self.remote = None
        log.msg("Anonymous user logged out")
    def perspective_getApplications(self):
        """Returns a list of Applications L{pyrope.model.local.Application} available on this server. """
        return self.server.getApplications()

class PyropeServer(pb.Root):
    """Acts as the main server class. Maintains a list of applications available to clients."""
    def __init__(self):
        self._applications = []
    def getApplications(self):
        apps = []
        for a in self._applications:
            apps.append(RemoteApplication(a))
        return apps
    def registerApplication(self, app):
        if app in self._applications:
            raise ApplicationAlreadyRegisteredException, "Applcation %s already registered" % app
        self._applications.append(app)

class PyropeService(internet.TCPServer):
    """A Pyrope application server. 
    Add your appication using L{registerApplication} and then call L{startup}."""
    def __init__(self, port=PORT):
        """Creates a Pyrope server and listens for anonymous connections (actually, those that supply anonymous/anonymous as the credentials) on port """
        ### startup server ###
        #listen for connections
        self._server = PyropeServer()
        realm = PyropeRealm()
        realm.server = self._server
        checker = checkers.InMemoryUsernamePasswordDatabaseDontUse()
        checker.addUser("anonymous", "anonymous") 
        p = portal.Portal(realm, [checker])
        internet.TCPServer.__init__(self, port, pb.PBServerFactory(p))
    
    def registerApplication(self, app):
        """Registers an application with the server.
        It just forwards app to servers registerApplication method.
        @param app: an Application (or subclass) instance.
        @type app: L{pyrope.model.local.Application}"""
        self._server.registerApplication(app)

    def startup(self):
        """ Starts listening for client connections """
        self.setServiceParent(application)

    def startService(self):
        log.msg("Pyrope server READY")

    def stopService(self):
        log.msg("Pyrope server SHUTTING DOWN")

application = service.Application("Pyrope")
service = PyropeService()
