#the order of imports is important here
from twisted.internet import wxreactor
wxreactor.install()
from pyrope.client.client import PyropeClient
    
if __name__ == "__main__":
    client = PyropeClient()
    client.startup()
