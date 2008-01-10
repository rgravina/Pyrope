"""Event handling"""
import wx
from twisted.spread import pb
from eskimoapps.utils.singleton import Singleton

class Event(pb.Copyable, pb.RemoteCopy):
    """Describes a client-side event. Data argument to constructor is optional (some events like a button click don't really have any data associated with them."""
    def __init__(self, widget, eventType, data=None):
        self.widget = widget
        self.eventType = eventType
        self.data = data
    def getStateToCopy(self):
        d = self.__dict__.copy()
        d["eventType"] = self.eventType.type
        return d
    def setCopyableState(self, state):
        self.__dict__ = state
        self.eventType = eval(state["eventType"])
pb.setUnjellyableForClass(Event, Event)

class EventFactory(object):
    _eventMap = {wx.EVT_BUTTON.typeId:"_getButtonEvent",
                 wx.EVT_TEXT.typeId:"_getTextEvent",
                 wx.EVT_TEXT_ENTER.typeId:"_getTextEnterEvent",
                 wx.EVT_CLOSE.typeId:"_getCloseEvent",
                 wx.EVT_SCROLL_CHANGED.typeId:"_getScrollEvnet",
                 wx.EVT_LISTBOX.typeId:"_getListBoxEvent",
                 wx.EVT_NOTEBOOK_PAGE_CHANGED.typeId:"_getNotebookPageChangedEvent",
                 wx.EVT_NOTEBOOK_PAGE_CHANGING.typeId:"_getNotebookPageChangingEvent"}

    @classmethod
    def create(cls, remote, wxEvent):
        #XXX:fixme
        return getattr(cls, cls._eventMap[wxEvent.GetEventType()])(remote, wxEvent)

    @classmethod
    def _getButtonEvent(self, remote, wxEvent):
        return Event(remote, ButtonEvent)
    @classmethod
    def _getTextEvent(self, remote, wxEvent):
        return Event(remote, TextEvent)
    @classmethod
    def _getTextEnterEvent(self, remote, wxEvent):
        return Event(remote, TextEnterEvent)
    @classmethod
    def _getCloseEvent(self, remote, wxEvent):
        return Event(remote, CloseEvent)
    @classmethod
    def _getScrollEvent(self, remote, wxEvent):
        return Event(remote, ScrollEvent)
    @classmethod
    def _getListBoxEvent(self, remote, wxEvent):
        return Event(remote, ListBoxEvent, data=wxEvent.GetSelection())
    @classmethod
    def _getNotebookPageChangedEvent(self, remote, wxEvent):
        return Event(remote, NotebookPageChangedEvent, data={"selection":wxEvent.GetSelection(), "oldSelection":wxEvent.GetOldSelection()})
    @classmethod
    def _getNotebookPageChangingEvent(self, remote, wxEvent):
        return Event(remote, NotebookPageChangingEvent, data={"selection":wxEvent.GetSelection(), "oldSelection":wxEvent.GetOldSelection()})

class ButtonEvent(object):
    type = "ButtonEvent"
    wxEventClass = wx.EVT_BUTTON

class CloseEvent(object):
    type = "CloseEvent"
    wxEventClass = wx.EVT_CLOSE

class TextEvent(object):
    type = "TextEvent"
    wxEventClass = wx.EVT_TEXT

class TextEnterEvent(object):
    type = "TextEnterEvent"
    wxEventClass = wx.EVT_TEXT_ENTER

class ScrollEvent(object):
    type = "ScrollEvent"
    wxEventClass = wx.EVT_SCROLL_CHANGED

class ListBoxEvent(object):
    type = "ListBoxEvent"
    wxEventClass = wx.EVT_LISTBOX

class NotebookPageChangedEvent(object):
    type = "NotebookPageChangedEvent"
    wxEventClass = wx.EVT_NOTEBOOK_PAGE_CHANGED

class NotebookPageChangingEvent(object):
    type = "NotebookPageChangingEvent"
    wxEventClass = wx.EVT_NOTEBOOK_PAGE_CHANGING
