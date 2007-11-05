# A simple "Hello World" example to test the Pyrope server
# Run me as:
# twistd -ny helloworld.py
from pyrope.server import application, service 
from pyrope.model import *

class HelloWorldApplicatioHandler(object):
    implements(IApplicationHandler)
    def start(self, perspective):
        log.msg("Started handler HelloWorldApplication")
        #create a frame on the client
        frame = Frame(perspective, None, title=u"Hello World")

#create Pyrope server
server = service.getServer()

#add in your app
app = Application("Hello World", handler=HelloWorldApplicatioHandler(),
                  description="A simple Hello World application for Pyrope. Displays one frame with the title set to \"Hello World\".")
server.registerApplication(app)

#start up server
service.startup()
