# A simple "Hello World" example to test the Pyrope server
# Run me as:
# twistd -ny helloworld.py
from twisted.application import service
from pyrope.server import server

application = service.Application("Hello World")
server = server.PyropeService()
server.setServiceParent(application)
