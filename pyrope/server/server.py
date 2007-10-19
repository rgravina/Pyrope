#Twisted imports
from twisted.cred import portal, checkers, credentials, error as credError
from twisted.spread import pb
from twisted.internet import defer
from twisted.application import internet
from twisted.python import log
from OpenSSL import SSL
#Axiom imports
from axiom.store import Store
from zope.interface import implements
#pyrope imports
from pyrope.errors import *
from loaders import *

class PyropeRealm:
    implements(portal.IRealm)
    def __init__(self, store):
        self.store = store

    def requestAvatar(self, avatarID, mind, *interfaces):
        assert pb.IPerspective in interfaces
        user = self.store.findFirst(User, User.username == avatarID)
        avatar = UserPerspective(user)
        avatar.attached(mind)
        return pb.IPerspective, avatar, lambda a=avatar:a.detached(mind)

class PasswordChecker(object):
    implements(checkers.ICredentialsChecker)
    credentialInterfaces = (credentials.IUsernameHashedPassword,)

    def __init__(self, store):
        self.store = store

    def requestAvatarId(self, credentials):
        username = credentials.username
        user = self.store.findFirst(User, User.username == username)        
        if user:
            if credentials.checkPassword(user.password):
                return defer.succeed(username)
        return defer.fail(
            credError.UnauthorizedLogin("Your logon details are incorrect"))

class UserPerspective(pb.Avatar):
    def __init__(self, user):
        self.user = user
    def attached(self, mind):
        self.remote = mind
    def detached(self, mind):
        self.remote = None
        #log the logout
        log.msg("User '"+self.user.username+"' logged out")

#use this command to generate a pem file
#openssl req -new -x509 -keyout server.pem -out server.pem -days 365 -nodes
class ServerContextFactory:
    def getContext(self):
        ctx = SSL.Context(SSL.SSLv23_METHOD)
        ctx.use_certificate_file('server.pem')
        ctx.use_privatekey_file('server.pem')
        return ctx

class PyropeService(internet.SSLServer):
    """ Accepts connections over SSL from the Pyrope client. """
    def __init__(self, port=8789):
        ### init database ###
        #create an in-memory store for storing data
        store = Store()
        #load sample data
        BasicDataLoader.load(store)

        ### startup server ###
        realm = PyropeRealm(store)
        #set up portal and authentication checker
        p = portal.Portal(realm)
        p.registerChecker(PasswordChecker(store))
        #listen for connections
        internet.SSLServer.__init__(self, port, pb.PBServerFactory(p), ServerContextFactory())

    def startService(self):
        log.msg("Pyrope server READY")

    def stopService(self):
        log.msg("Pyrope server SHUTTING DOWN")
