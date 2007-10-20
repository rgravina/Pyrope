# Pyrope client
# Robert Gravina
# This client uses the Model-View-Presenter pattern detailed here:
# http://wiki.wxpython.org/index.cgi/ModelViewPresenter

from pyrope.client.presenters import ApplicationPresenter
from twisted.internet import reactor
from pyrope.config import HOST, PORT

class PyropeClient(object):
    def __init__(self,  host=HOST, port=PORT):
        self._host = host
        self._port = port
        
    def startup(self):
        reactor.registerWxApp(ApplicationPresenter.getInstance(self._host, self._port).view)
        ApplicationPresenter.getInstance().start()
        reactor.run(True)
