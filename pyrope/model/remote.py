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
    def __init__(self, app, widget, remote, handlers):
        self.app = app           #RemoteApplicationHandler
        self.widget = widget     #wxWindow    
        self.remote = remote     #server-side Pyrope widget refernce  
        self.boundEvents = []    #bound Pyrope events, e.g. EventClose
        for event in handlers:
            eventClass = eval(event)
            self.boundEvents.append(eventClass)
            self.widget.Bind(eventClass.wxEventClass, self.handleEvent)            
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
    def handleEvent(self, event):
        eventData = EventFactory.create(self.remote, event)
        self.remote.callRemote("handleEvent", eventData)
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
    pass

#class PanelReference(WindowReference):
#    pass

class TextBoxReference(WindowReference):
    def remote_getData(self):
        return self.widget.GetValue()
    def remote_setData(self, data):
        return self.widget.SetValue(data)
#    def onText(self, event):
#        self.remote.callRemote("updateData", self.widget.GetValue())

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
        print "item selected"
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

class MessageDialogBuilder(TopLevelWindowBuilder):
    widgetClass = wx.MessageDialog
    referenceClass = DialogReference

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
        frame = widgetData.constructorData["parent"]
        frame.SetToolBar(widget)
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

class PNGImageBuilder(WidgetBuilder):
    widgetClass = wx.Image
    referenceClass = WindowReference
    def createLocalReference(self, app, widgetData):
        parent = app.widgets[widgetData.otherData["parent"]]
        stream = cStringIO.StringIO(widgetData.otherData["data"])
        bitmap = BitmapFromImage(ImageFromStream(stream))
        localRef = self.referenceClass(app, bitmap, widgetData.remoteWidgetReference, widgetData.eventHandlers)
        app.widgets[widgetData.remoteWidgetReference] = localRef.widget
        wx.StaticBitmap(parent, wx.ID_ANY, bitmap)
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
        #create and return the local pb.Referenceable that will manage this widget
        return builder.createLocalReference(app, widgetData)

class RemoteApplicationHandler(pb.Referenceable):
    def __init__(self, app, appPresenter):
        self.app = app
        self.appPresenter = appPresenter
        #only for wx.Frame and wx.Dialog
        self.topLevelWindows = []
        self.widgets = {}
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
