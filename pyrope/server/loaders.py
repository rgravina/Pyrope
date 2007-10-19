""" Contains loaders for initialising the database. """
from zope.interface import Interface, implements, classProvides
from twisted.python import log
from pyrope.model.local import *

class IDataLoader(Interface):
    """Loads initial Pyrope data into an Axiom data store"""
    def load(self, store):
        """Load data into store"""

class BasicDataLoader:
    """ Adds a single admin user account """
    classProvides(IDataLoader)
    @classmethod
    def load(cls, store):
        store.transact(cls._load, store)
    @classmethod
    def _load(cls, store):    
        #create default users if not already there
        if not store.findFirst(User):
            User(store=store, username=u"admin", password=u"admin")
