# Demo application server
# Run me as:
# twistd -ny demo.py
from pyrope.server import application, service 
from pyrope.examples.helloworld import HelloWorldApplication
from pyrope.examples.addressbook import AddressBookApplication
from pyrope.examples.widgets import WidgetsApplication
from pyrope.examples.ticker import TickerApplication
from pyrope.examples.chat import ChatApplication

#add in your apps
service.registerApplication(HelloWorldApplication())
service.registerApplication(AddressBookApplication())
service.registerApplication(WidgetsApplication())
service.registerApplication(TickerApplication())
service.registerApplication(ChatApplication())

#start up server
service.startup()
