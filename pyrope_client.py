#the order of imports is important here
from twisted.internet import wxreactor
wxreactor.install()
from pyrope.client.client import PyropeClient

def run():
    client = PyropeClient()
    
if __name__ == "__main__":
    run()
