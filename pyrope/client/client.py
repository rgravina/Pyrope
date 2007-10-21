# Pyrope client
# Robert Gravina
# This client uses the Model-View-Presenter pattern detailed here:
# http://wiki.wxpython.org/index.cgi/ModelViewPresenter

from pyrope.client.presenters import PyropeApplicationPresenter
from twisted.internet import reactor
from pyrope.config import *

class PyropeClient(object):
    def __init__(self,  host=HOST, port=PORT):
        app = PyropeApplicationPresenter.getInstance("Pyrope", host, port)
        reactor.registerWxApp(app.view)
        app.start()
        reactor.run(True)
