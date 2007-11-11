#Twisted imports
from twisted.cred import portal, checkers
from twisted.spread import pb
from twisted.application import internet
from twisted.application import service
from twisted.python import log
from zope.interface import Interface, Attribute, implements
#Pyrope imports
from pyrope.errors import *
from pyrope.model import *

class PyropeRealm:
    implements(portal.IRealm)
    def requestAvatar(self, avatarID, mind, *interfaces):
        assert pb.IPerspective in interfaces
        avatar = AnonymousUserPerspective()
        avatar.server = self.server
        avatar.attached(mind)
        return pb.IPerspective, avatar, lambda a=avatar:a.detached(mind)

class AnonymousUserPerspective(pb.Avatar):
    """Pyrope accepts anonymous connnections from Pyrope clients. We want this so users connecting to the server can get a list of applications and also
    so authentication can be dealt with on a per-application basis."""
    #TODO: authentication on a per-application basis
    def attached(self, mind):
        self.remote = mind
        log.msg("Anonymous user logged on")
    def detached(self, mind):
        self.remote = None
        log.msg("Anonymous user logged out")
    def perspective_getApplications(self):
        return self.server.getApplications()

    #TODO: move these methods somewhere more appropriate, like the Pyrope GUI classes
    def createFrame(self, frame):
        self.remote.callRemote("createFrame", frame)
    def show(self, id):
        self.remote.callRemote("show", id)
    def createPanel(self, panel):
        self.remote.callRemote("createPanel", panel)
    def createButton(self, button):
        self.remote.callRemote("createButton", button)
    def createLabel(self, label):
        self.remote.callRemote("createLabel", label)
    def createNotebook(self, notebook):
        self.remote.callRemote("createNotebook", notebook)
    def addPage(self, notebookID, panelID, title):
        self.remote.callRemote("addPage", notebookID, panelID, title)
    def createBoxSizer(self, sizer):
        self.remote.callRemote("createBoxSizer", sizer)

class PyropeServer(pb.Root):
    """Register applications and get a list of them."""
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
    """A Pyrope application server. After creating a PyropeServer instance, add your appication using 
    registerApplication and call startup."""
    def __init__(self, port=8789):
        ### startup server ###
        #listen for connections
        self._server = PyropeServer()
        realm = PyropeRealm()
        realm.server = self._server
        checker = checkers.InMemoryUsernamePasswordDatabaseDontUse()
        checker.addUser("anonymous", "anonymous") 
        p = portal.Portal(realm, [checker])
        internet.TCPServer.__init__(self, port, pb.PBServerFactory(p))
    
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
