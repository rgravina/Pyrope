from axiom.item import Item
from axiom.attributes import text

class User(Item):
    username = text()
    password = text()
