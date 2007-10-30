# A simple "Hello World" example to test the Pyrope server
# Run me as:
# twistd -ny helloworld.py
from pyrope.server import application, service 
from pyrope.model import Application
from zope.interface import implements, classProvides

#create Pyrope server
server = service.getServer()

#add in your app
app = Application("Hello World", description="A simple Hello World application for Pyrope. Displays one frame with the title set to \"Hello World\".")
server.registerApplication(app)

#start up server
service.startup()