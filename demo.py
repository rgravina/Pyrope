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
        frame.show()
        
class SimpleWidgetApplicatioHandler(object):
    implements(IApplicationHandler)
    def start(self, perspective):
        log.msg("Started handler SimpleWidgetApplicatioHandler")
        frame = Frame(perspective, None, title=u"Simple Widget Demo")
        frame.show()
        frame2 = Frame(perspective, frame, title=u"Simple Widget Demo2")
        frame2.show()

class AddressBookApplicatioHandler(object):
    implements(IApplicationHandler)
    def start(self, perspective):
        log.msg("Started handler AddressBookApplicatioHandler")
        frame = Frame(perspective, None, title=u"Address Book Demo")
        frame.show()

#create Pyrope server
server = service.getServer()

#add in your app
app = Application("Hello World", handler=HelloWorldApplicatioHandler(),
                  description="A simple Hello World application for Pyrope. Displays one frame with the title set to \"Hello World\".")
server.registerApplication(app)
app = Application("Simple Widget Demo", handler=SimpleWidgetApplicatioHandler(),
                  description="Demonstrates the various widgets supported by Pyrope.")
server.registerApplication(app)
app = Application("Address Book Demo", handler=AddressBookApplicatioHandler(),
                  description="An address book application.")
server.registerApplication(app)

#start up server
service.startup()
