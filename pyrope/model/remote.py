"""The Remote (i.e. usually client-side) model."""
import wx
import wxaddons.sized_controls as sc
from wx import ImageFromStream, BitmapFromImage
import cStringIO
from twisted.python import log
from twisted.spread.flavors import NoSuchMethod
from pyrope.model.shared import *
from pyrope.model.events import *

from zope.interface import Interface, Attribute, implements

class RemoteApplication(pb.Copyable, pb.RemoteCopy):
    """Describes a Pyrope application, with a reference to the application handler (pb.Referenceable on the server, pb.RemoteReference on the client)"""
    def __init__(self, app):
        self.name = app.name
        self.description = app.description
        self.server = app
pb.setUnjellyableForClass(RemoteApplication, RemoteApplication)

class WidgetConstructorDetails(pb.Copyable, pb.RemoteCopy):
    """Describes a information needed by the client to create a local wxWidget which represents a server-side Pyrope widget. 
    It is a U{Parameter Object<http://www.refactoring.com/catalog/introduceParameterObject.html>}"""
    def __init__(self, remoteWidgetReference, type, constructorData, otherData=None, styleData=None, children=None, eventHandlers=None):
        self.remoteWidgetReference = remoteWidgetReference
        self.type = type
        self.constructorData = constructorData
        self.otherData = otherData
        self.styleData = styleData
        self.children = children
        self.eventHandlers = eventHandlers
pb.setUnjellyableForClass(WidgetConstructorDetails, WidgetConstructorDetails)

class Changeset(pb.Copyable, pb.RemoteCopy):
    """Describes changes to widget properties. Order of changes made is not preserved. Clear should be called after changeset has been 
    sent to server. 
    
    Changeset entry: widget : (property name, value)"""
    def __init__(self):
        self.changes = {}
    def addChange(self, widget, propertyName, newValue):
        """Adds chage to changeset."""
        self.changes[widget] = (propertyName, newValue)
    def clear(self):
        self.changes.clear()
    def apply(self):
        """Apply changes in changeset. Iterates through each change in the changeset and applies them."""
        for widget, (propName, value) in self.changes.items():
            setattr(widget, propName, value)
    def isEmpty(self):
        """@return: True is changes dict has some entires, False otherwise."""
        if len(self.changes):
            return False
        return True
pb.setUnjellyableForClass(Changeset, Changeset)

class PyropeReferenceable(pb.Referenceable):
    """Subclasses pb.Referenceable so that it calls self.widget.somemethod when remote_somemethod connot be found.
    This makes it simpler to wrap methods on wxWidgets classes."""
    def remoteMessageReceived(self, broker, message, args, kw):
        """ Calls self.widget.somemethod when remote_somemethod connot be found"""
        try:
            return pb.Referenceable.remoteMessageReceived(self, broker, message, args, kw)
        except NoSuchMethod:
            return getattr(self.widget, message)()

def returnWxPythonObject(object):
    """Use this method when returning objects from wxPython methods. Why? E.g. say a wxPython returns a wxPoint, we can't send this directly over the netowork 
    (Twisted Perspective Broker won't allow it for security reasons), so we can just send a tuple with the coordinates instead. The default behaviour is 
    just to return the passed argument"""
    def returnDefault(object):
        return object
    getattr(returnWxPythonObject, "return"+object.__class__.__name__, returnDefault)
    def returnPoint(object):
        return (object.x, object.y)
 
class WindowReference(PyropeReferenceable):
    """Manages a local wxWindow"""
    #list of events which indicate that the data has changed in this control
    #e.g. wx.EVT_TEXT for a TextBox. Sublasses should override this attribute
    #so things don't break, this class has an empty list
    changeEvents = []    
    def __init__(self, app, widget, remote, handlers):
        self.app = app           #RemoteApplicationHandler
        self.widget = widget     #wxWindow    
        self.remote = remote     #server-side Pyrope widget refernce  
        self.boundEvents = []    #bound Pyrope events, e.g. EventClose
        self.children = []       #references of children

        #bind all event handlers server is interested in
        for event in handlers:
            eventClass = eval(event)
            self.boundEvents.append(eventClass)
            self.widget.Bind(eventClass.wxEventClass, self.handleEvent)

        #we need to listen for changes to the widget, so that a changeset can be generated
        for event in self.changeEvents:
            self.widget.Bind(event, self.recordChange)
            

    def recordChange(self, event):
        """Records change in changeset instance, and passes the event on to the next handler."""
        propertyValueTuple = self.getChangeData(event)
        if propertyValueTuple:
            self.app.changeset.addChange(self.remote, propertyValueTuple[0], propertyValueTuple[1])
        event.Skip()

    def getChangeData(self, event):
        """Given an event instance, this method should figure out what property should be updated with what data.
         @return: (property name, value)"""
         #TODO: implement something for wxWindow here
    
    #closing and detroying window
    def remote_Destroy(self):
        self._destroy()
    def _destroy(self):
        self.widget.Destroy()
    def onClose(self, event):
        if CloseEvent in self.boundEvents:
            self.handleEvent(event)
        else:
            #if the programmer hasnt handled the close event specifically, then the default behaviour is to close the form
            self._destroy()
            
    #event handling
    def handleEvent(self, event):
        """This gets called when an event occurs that the server is interested in. We send the server the event data and 
        also the changes that have occurred since the last change."""
        #get event data for this event type
        eventData = EventFactory.create(self.remote, event)
        #send event and changeset data
        self.remote.callRemote("handleEvent", eventData, self.app.changeset)
        #clear changeset
        self.app.changeset.clear()
    
    #other methods
    def remote_Centre(self, direction, centreOnScreen): 
        dir = direction
        if centreOnScreen:
            dir | wx.CENTRE_ON_SCREEN
        return self.widget.Centre(direction = dir)
    def remote_ClientToScreen(self, (x, y)):
        return self.widget.ClientToScreenXY(x, y)
    def remote_SetBackgroundColour(self, colour):
        return self.widget.SetBackgroundColour(colour)

class TopLevelWindowReference(WindowReference):
    def _destroy(self):
        """Check to see if this is the last window open (for this app) and if so, call shutdown on the RemoteApplicationHandler instance.
        Finally, destroy the widget."""
        self.app.topLevelWindows.remove(self.widget)
        if not self.app.topLevelWindows:
            self.app.shutdown()
        self.widget.Destroy()

class FrameReference(TopLevelWindowReference):
    pass
#class SizedFrameReference(TopLevelWindowReference):
#    pass

class DialogReference(TopLevelWindowReference):
    def remote_ShowModal(self):
        return self.widget.ShowModal()

class TextEntryDialogReference(DialogReference):
    def remote_showModalAndGetValue(self):
        id = self.widget.ShowModal()
        val = self.widget.GetValue()
        return (id, val)
#class PanelReference(WindowReference):
#    pass

class TextBoxReference(WindowReference):
    changeEvents = [wx.EVT_TEXT]
    def getChangeData(self, event):
        if event.GetEventType() == wx.EVT_TEXT.typeId:
            return ("value", self.widget.GetValue())
    def remote_getData(self):
        return self.widget.GetValue()
    def remote_setData(self, data):
        return self.widget.SetValue(data)

class LabelReference(WindowReference):
    def remote_getData(self):
        return self.widget.GetLabel()
    def remote_setData(self, data):
        return self.widget.SetLabel(data)

class SliderReference(WindowReference):
    def remote_getData(self):
        return self.widget.GetValue()
    def remote_setData(self, data):
        return self.widget.SetValue(data)

class GaugeReference(WindowReference):
    def remote_getData(self):
        return self.widget.GetValue()
    def remote_setData(self, data):
        return self.widget.SetValue(data)

class ControlWithItemsReference(WindowReference):
    def remote_getData(self):
        return self.widget.GetSelection()
    def remote_setData(self, data):
        self.widget.Clear()
        for item in data:
            self.widget.Append(item)
        self.widget.Update()

class MenuBarReference(WindowReference):
    def onMenu(self, event):
        print event.GetEventObject()

class MenuItemReference(object):
    def __init__(self, menuBarRef, widget):
        self.menuBarRef = menuBarRef
        self.widget = widget
    def onMenu(self, event):
        self.menuBarRef.remote.callRemote("menuItemSelected", self.widget.GetId())

class StatusBarReference(WindowReference):
    def remote_getData(self):
        return self.widget.GetValue()
    def remote_setData(self, data):
        self.widget.SetFieldsCount(data["numFields"])
        for index, text in data["fields"].items():
            self.widget.SetStatusText(text, index)
        
############
# Builders #
############
class WidgetBuilder(object):
    def replaceParent(self, app, widgetData):
        parent = widgetData.constructorData["parent"]
        if parent:
            widget =  app.widgets[parent] 
            if isinstance(widget, (sc.SizedFrame, sc.SizedDialog)):
                widgetData.constructorData["parent"] = widget.GetContentsPane()
            else:
                widgetData.constructorData["parent"] = widget
    
    def createLocalReference(self, app, widgetData):
        #XXX: this will break if called from a WidgetBuilder instance!
        if widgetData.styleData:
            widgetData.constructorData["style"] = widgetData.styleData
        window = self.widgetClass(**widgetData.constructorData)
        localRef = self.referenceClass(app, window, widgetData.remoteWidgetReference, widgetData.eventHandlers)
        app.widgets[widgetData.remoteWidgetReference] = localRef.widget
        if widgetData.children:
            for childData in widgetData.children:
                childRef = WidgetFactory.create(app, childData)
                #server needs to know about child reference
                childData.remoteWidgetReference.callRemote("updateRemote", childRef)
                #add to localRef children
                localRef.children.append(childRef)
        return localRef

class TopLevelWindowBuilder(WidgetBuilder):
    def createLocalReference(self, app, widgetData):
        localRef = WidgetBuilder.createLocalReference(self, app, widgetData)
        localRef.widget.Bind(wx.EVT_CLOSE, localRef.onClose)
        app.topLevelWindows.append(localRef.widget)
        return localRef

#class FrameBuilder(TopLevelWindowBuilder):
#    widgetClass = wx.Frame
#    referenceClass = FrameReference

#class MiniFrameBuilder(TopLevelWindowBuilder):
#    widgetClass = wx.MiniFrame
#    referenceClass = FrameReference

#class DialogBuilder(TopLevelWindowBuilder):
#    widgetClass = wx.Dialog
#    referenceClass = DialogReference

class DialogBuilder(TopLevelWindowBuilder):
    widgetClass = sc.SizedDialog
    referenceClass = DialogReference
    def replaceParent(self, app, widgetData):
        parent = widgetData.constructorData["parent"]
        if parent:
            widgetData.constructorData["parent"] = app.widgets[parent] 

class MessageDialogBuilder(DialogBuilder):
    widgetClass = wx.MessageDialog
    referenceClass = DialogReference

class TextEntryDialogBuilder(DialogBuilder):
    widgetClass = wx.TextEntryDialog
    referenceClass = TextEntryDialogReference
 
class FrameBuilder(TopLevelWindowBuilder):
    widgetClass = sc.SizedFrame
    referenceClass = FrameReference
    def createLocalReference(self, app, widgetData):
        localRef = TopLevelWindowBuilder.createLocalReference(self, app, widgetData)
        widget = localRef.widget.GetContentsPane()
        widget.SetSizerType(widgetData.otherData["sizerType"])
        #create menus
        menuData = widgetData.otherData["menuBar"]
        if menuData:
            menuBarRef = WidgetFactory.create(app, menuData)
            menuData.remoteWidgetReference.callRemote("updateRemote", menuBarRef)
            localRef.widget.SetMenuBar(menuBarRef.widget)
        return localRef

class PanelBuilder(WidgetBuilder):
    widgetClass = sc.SizedPanel
    referenceClass = WindowReference
    def createLocalReference(self, app, widgetData):
        localRef = WidgetBuilder.createLocalReference(self, app, widgetData)
        widget = localRef.widget
        widget.SetSizerType(widgetData.otherData["sizerType"])
        return localRef

class TextBoxBuilder(WidgetBuilder):
    widgetClass = wx.TextCtrl
    referenceClass = TextBoxReference
#    def createLocalReference(self, app, widgetData):
#        localRef = WidgetBuilder.createLocalReference(self, app, widgetData)
#        localRef.widget.Bind(wx.EVT_TEXT, localRef.onText)
#        return localRef

class LabelBuilder(WidgetBuilder):
    widgetClass = wx.StaticText
    referenceClass = LabelReference

class ButtonBuilder(WidgetBuilder):
    widgetClass = wx.Button
    referenceClass = WindowReference
    def createLocalReference(self, app, widgetData):
        localRef = WidgetBuilder.createLocalReference(self, app, widgetData)
        widget = localRef.widget
        if widgetData.otherData["default"]:
            widget.SetDefault()
        return localRef

class BitmapButtonBuilder(ButtonBuilder):
    widgetClass = wx.BitmapButton
    referenceClass = WindowReference
    def createLocalReference(self, app, widgetData):
        stream = cStringIO.StringIO(widgetData.otherData["image"])
        bitmap = BitmapFromImage(ImageFromStream(stream))
        widgetData.constructorData["bitmap"] = bitmap
        return ButtonBuilder.createLocalReference(self, app, widgetData)

class ChoiceBuilder(WidgetBuilder):
    widgetClass = wx.Choice
    referenceClass = ControlWithItemsReference

class CheckBoxBuilder(WidgetBuilder):
    widgetClass = wx.CheckBox
    referenceClass = WindowReference

class GaugeBuilder(WidgetBuilder):
    widgetClass = wx.Gauge
    referenceClass = GaugeReference
    def createLocalReference(self, app, widgetData):
        localRef = WidgetBuilder.createLocalReference(self, app, widgetData)
        widget = localRef.widget
        widget.SetValue(widgetData.otherData["value"])
        return localRef

class SliderBuilder(WidgetBuilder):
    widgetClass = wx.Slider
    referenceClass = SliderReference

class ListBoxBuilder(WidgetBuilder):
    widgetClass = wx.ListBox
    referenceClass = ControlWithItemsReference

class CheckListBoxBuilder(WidgetBuilder):
    widgetClass = wx.CheckListBox
    referenceClass = WindowReference

class SpinnerBuilder(WidgetBuilder):
    widgetClass = wx.SpinCtrl
    referenceClass = WindowReference
    def createLocalReference(self, app, widgetData):
        localRef = WidgetBuilder.createLocalReference(self, app, widgetData)
        widget = localRef.widget
        range = widgetData.otherData["range"]
        widget.SetRange(range[0],range[1])
        return localRef

class RadioBoxBuilder(WidgetBuilder):
    widgetClass = wx.RadioBox
    referenceClass = WindowReference

class BoxBuilder(WidgetBuilder):
    widgetClass = wx.StaticBox
    referenceClass = WindowReference

class LineBuilder(WidgetBuilder):
    widgetClass = wx.StaticLine
    referenceClass = WindowReference

class MenuBarBuilder(WidgetBuilder):
    widgetClass = wx.MenuBar
    referenceClass = MenuBarReference
    def replaceParent(self, app, widgetData):
        pass
    def createLocalReference(self, app, widgetData):
        menuBar = self.widgetClass(**widgetData.constructorData)
        localRef = self.referenceClass(app, menuBar, widgetData.remoteWidgetReference, widgetData.eventHandlers)
        app.widgets[widgetData.remoteWidgetReference] = localRef.widget
        #create menus
        for menu in widgetData.otherData["menus"]:
            wxMenu = wx.Menu()
            for item in menu.items:
                form = app.widgets[widgetData.otherData["form"]]
                wxMenuItem = wx.MenuItem(wxMenu, item.id, item.text, item.help)
                itemRef = MenuItemReference(localRef, wxMenuItem)
                wx.EVT_MENU(form, item.id, itemRef.onMenu)
                wxMenu.AppendItem(wxMenuItem)
            menuBar.Append(wxMenu, menu.title)
        return localRef

class ToolBarBuilder(WidgetBuilder):
    widgetClass = wx.ToolBar
    referenceClass = WindowReference
    def replaceParent(self, app, widgetData):
        parent = widgetData.constructorData["parent"]
        if parent:
            widget =  app.widgets[parent] 
            widgetData.constructorData["parent"] = widget
    def createLocalReference(self, app, widgetData):
        localRef = WidgetBuilder.createLocalReference(self, app, widgetData)
        widget = localRef.widget
#        bitmap = wx.Bitmap("images/dot-red.png", wx.BITMAP_TYPE_PNG)
        for label, image in widgetData.otherData["tools"]:
            stream = cStringIO.StringIO(image)
            bitmap = BitmapFromImage(ImageFromStream(stream))
            widget.AddLabelTool(wx.ID_ANY, label, bitmap)
        frame = widgetData.constructorData["parent"]
        frame.SetToolBar(widget)
        widget.Realize()
        return localRef

class StatusBarBuilder(WidgetBuilder):
    widgetClass = wx.StatusBar
    referenceClass = StatusBarReference
    def replaceParent(self, app, widgetData):
        parent = widgetData.constructorData["parent"]
        if parent:
            widget =  app.widgets[parent] 
            widgetData.constructorData["parent"] = widget
    def createLocalReference(self, app, widgetData):
        localRef = WidgetBuilder.createLocalReference(self, app, widgetData)
        widget = localRef.widget
        widget.SetFieldsCount(widgetData.otherData["numFields"])
        for index, text in widgetData.otherData["fields"].items():
            widget.SetStatusText(text, index)
        frame = widgetData.constructorData["parent"]
        frame.SetStatusBar(widget)
        return localRef

class ImageBuilder(WidgetBuilder):
    widgetClass = wx.Image
    referenceClass = WindowReference
    def createLocalReference(self, app, widgetData):
        parent = app.widgets[widgetData.otherData["parent"]]
        stream = cStringIO.StringIO(widgetData.otherData["data"])
        bitmap = BitmapFromImage(ImageFromStream(stream))
        localRef = self.referenceClass(app, bitmap, widgetData.remoteWidgetReference, widgetData.eventHandlers)
        app.widgets[widgetData.remoteWidgetReference] = localRef.widget
        #if parent is a panel, dispay the image
        if isinstance(parent, wx.Panel):
            wx.StaticBitmap(parent, wx.ID_ANY, bitmap)
        return localRef

class SplitterBuilder(WidgetBuilder):
    widgetClass = wx.SplitterWindow
    referenceClass = WindowReference
    def createLocalReference(self, app, widgetData):
        localRef = WidgetBuilder.createLocalReference(self, app, widgetData)
        widget = localRef.widget
        #if no children, return
        if not localRef.children:
            pass
        #if only one child, use initialise
        elif len(localRef.children) is 1:
            widget.Initialize(localRef.children[0].widget)
        #if two, spit horizontally or vertically
        elif widgetData.otherData["mode"] is "horizontal":
            widget.SplitHorizontally(localRef.children[0].widget, localRef.children[1].widget)
        else:
            widget.SplitVertically(localRef.children[0].widget, localRef.children[1].widget)
        widget.SetMinimumPaneSize(widgetData.otherData["minimumPaneSize"])
        return localRef

class NotebookBuilder(WidgetBuilder):
    widgetClass = wx.Notebook
    referenceClass = WindowReference
    def createLocalReference(self, app, widgetData):
        localRef = WidgetBuilder.createLocalReference(self, app, widgetData)
        nb = localRef.widget
        pages = widgetData.otherData["pages"]
        for title, page in pages:
            pageWidget = app.widgets[page] 
            nb.AddPage(pageWidget, title)
        return localRef
    
##################
# Widget Factory #
##################
class WidgetFactory(object):
    """A Factory that produces wxWidgets based on the class of the remote Pyrope widget passed to the constructor."""
    @classmethod
    def create(cls, app, widgetData):
        builder = eval(widgetData.type+"Builder")()
        #if the remote widget has a parent (supplied as a pb.RemoteReference) replace the attribute with the coressponding wxWindow which is it's real parent
        builder.replaceParent(app, widgetData)
        #create the local pb.Referenceable that will manage this widget
        return builder.createLocalReference(app, widgetData)
        #add to list of localrefs
#        app.localRefs.append(localRef)
#        return localRef
    
class RemoteApplicationHandler(pb.Referenceable):
    def __init__(self, app, appPresenter):
        self.app = app
        self.appPresenter = appPresenter
        #only for wx.Frame and wx.Dialog
        self.topLevelWindows = []    #wxWidgets
        self.widgets = {}            #RemoteReference (Pyrope Widget) -> wxWidget
#        self.localRefs = []         #local references for widgets
        self.changeset = Changeset() #when changes are pending, this should hold them
    def shutdown(self):
        def _shutdown(result):
            self.appPresenter.shutdownApplication(self.app)
        return self.app.server.callRemote("shutdownApplication", self).addCallback(_shutdown)
    def remote_createWidget(self, widgetData):
        #create widget and local proxy
        #return pb.RemoteReference to server
        return WidgetFactory.create(self, widgetData)

class PyropeClientHandler(pb.Referenceable):
    pass
