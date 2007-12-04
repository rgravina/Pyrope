# Demo application server
# Run me as:
# twistd -ny demo.py
from pyrope.server import application, service 
from pyrope.examples.helloworld import HelloWorldApplication
from pyrope.examples.addressbook import AddressBookApplication
from pyrope.examples.widgets import WidgetsApplication

#add in your apps
service.registerApplication(HelloWorldApplication())
service.registerApplication(AddressBookApplication())
service.registerApplication(WidgetsApplication())

#start up server
service.startup()
