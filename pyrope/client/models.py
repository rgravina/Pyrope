from pyrope.singletonmixin import Singleton
from twisted.cred import credentials

class ApplicationModel(Singleton):
    #server perspective/avatar
    perspective = None
    #an object which can recieve callbacks from the server
    localHandler = None
    #User object representing the logged on user
    user = None
    host = None
    port = None
    
    def __init__(self, host, port, username="", password=""):
        self.host = host
        self.port = port
        self.credentials = username, password
    
    def _setCredentials(self, (username, password)):
        self._credentials = credentials.UsernamePassword(username, password)
    def _getCredentials(self):
        return self._credentials
    credentials = property(_getCredentials, _setCredentials)
    
    def _getUsername(self):
        return self._credentials.username
    username = property(_getUsername, None)
    def _getPassword(self):
        return self._credentials.password
    password = property(_getPassword, None)
