"""The Local (i.e. usually server-side) model."""
import wx
from zope.interface import implements, Interface, Attribute
from twisted.spread import pb
from twisted.python import log
from twisted.internet.defer import inlineCallbacks
from pyrope.model.shared import *
from pyrope.model.remote import *
from pyrope.model.events import *
from pyrope.errors import RemoteResourceNotCreatedException

class IApplication(Interface):
    """A Pyrope application"""
    def start(self, handler):
        """Start up the application"""

class RunningApplication(object):
    """Represents an instance of a running application.
    At this stage there are no methods, it just acts as a parameter object."""
    def __init__(self, perspective, handler):
        self.perspective = perspective     #users perpective 
        self.handler = handler             #client-side application handler
        self.widgets = []                  #widgets in this instance
    
class Application(pb.Viewable):
    """Base class for user applications. Users should subclass this and override at least L{start}."""
    implements(IApplication)
    def __init__(self, name, description=None):
        self.name = name
        self.description = description
        self.runningApplications = {}
    def view_startApplication(self, perspective, handler):
        """Called by the client when a user wants to start up a new application."""
        #save the perspective for later use
        #TODO: make sure perspective is removed when app is closed
        run = RunningApplication(perspective, handler)
        self.runningApplications[handler] = run
        #simply call the start method
        self.start(run)
    def view_shutdownApplication(self, perspective, handler):
        """Called by the client when a user wants to shutdown the application."""
        run =  self.runningApplications[handler]
        #simply call the shutdown method
        self.shutdown(run)
        del self.runningApplications[handler]
    def start(self, run):
        """Subclasses should start their applications here"""
        pass
    def shutdown(self, run):
        """Subclasses should put any shutdown code here"""
        pass
        
class PyropeWidget(pb.Referenceable):
    type = "PyropeWidget"
    def __init__(self, run):
        self.run = run
        run.widgets.append(self)
        #the remote reference will be set when the client supplies it
        self.remote = None
        #for event handling
        self.eventHandlers = {}
    @inlineCallbacks
    def createRemote(self):
        #creates remote widget, and gets a pb.RemoteReference to it's client-side proxy
        self.remote = yield self.run.handler.callRemote("createWidget", self.getConstructorDetails())
    def callRemote(self, functName, *args):
        if self.remote:
            return self.remote.callRemote(functName, *args)
        else:
            raise RemoteResourceNotCreatedException, "You must call createRemote before calling this method"
    def bind(self, event, handlerFunction):
        self.eventHandlers[event] = handlerFunction
    def remote_handleEvent(self, event):
        """Called by client when an event has been fired. """
        #update local cached data
#        event.widget.handleEvent(event)
        #call event handler
        #TODO: support multiple handlers
        self.eventHandlers[event.eventType](event)
    def remote_updateData(self, data):
        #update local cached data
        self.updateData(data)
    def remote_updateRemote(self, remote):
        self.remote = remote

class Window(PyropeWidget):
    type = "Window"
    def __init__(self, run, parent, position=DefaultPosition, size=DefaultSize):
        PyropeWidget.__init__(self, run)
        self.parent = parent
        if parent != None:
            parent.children.append(self)
        self.pos = position
        self.size = size
        #other props
        self.children = []
        self.wxStyle = 0
    def getConstructorDetails(self):
        """Creates an instance of WidgetConstructorDetails, with all the details the client needs to create 
        the client-side version of this widget"""
        return WidgetConstructorDetails(self, self.type, self._getConstructorData(), self._getOtherData(), self._getStyleData(), 
                                        self._getChildren(), self._getEventHandlers())
    def _getConstructorData(self):
        d = {}
        d["parent"] = self.parent
        d["pos"] = self.pos
        d["size"] = self.size
        return d
    def _getOtherData(self):
        pass
    def _addStyleToggle(self, attr, attrStr):
        if attr:
            self.wxStyle = self.wxStyle | self._props[attrStr]
        else: 
            self.wxStyle = self.wxStyle ^ self._props[attrStr]
    def _addStyleVal(self, attr, attrStr):
        if attr:
            self.wxStyle = self.wxStyle | self._props[attrStr]
    def _getStyleData(self):
        return self.wxStyle
#        wxStyle=0
        #TODO: avoid creating a new instance each time
#        decorator = self.decoratorClass(self.styles)
#        return decorator.toWxStyle()
    def _getEventHandlers(self):
        eventHandlers = []
        for event, fn in self.eventHandlers.items():
            eventHandlers.append(event.type)
        return eventHandlers
    def _getChildren(self):
        children = []
        for child in self.children:
            children.append(child.getConstructorDetails())
        return children
#    def handleEvent(self, event):
#        """Default response to an event is to ignore it. Implement useful behaviour in subsclasses (e.g. for TextBox, on a EventText, update the textboxes value attribute)"""
#        pass
#    def updateData(self, data):
#        pass
    def syncWithRemote(self):
        def _done(data):
            self.setData(data)
        return self.callRemote("getData").addCallback(_done)
    def syncWithLocal(self):
        return self.callRemote("setData", self.getData())
    def clientToScreen(self, point):
        return self.callRemote("ClientToScreen", point)
    def hide(self):
        return self.callRemote("Hide")
    def show(self):
        return self.callRemote("Show")
    def centre(self, direction=wx.BOTH, centreOnScreen=False):
        return self.callRemote("Centre", direction, centreOnScreen)
    def destroy(self):
        return self.callRemote("Destroy")
    def disable(self):
        return self.callRemote("Disable")
    def enable(self):
        return self.callRemote("Enable")

#    def GetBackgroundColour(self):
#        #simply return the background colour
#        return self._backgroundColour
#    def SetBackgroundColour(self, colour):
#        #set the local background colour
#        self._backgroundColour = colour
#        #set remote
#        return self.callRemote("SetBackgroundColour", colour)
#    #XXX: this doesn't work for setter!
#    backgroundColour = property(GetBackgroundColour, SetBackgroundColour)


######################
# Frames and Dialogs #
######################

#class Frame(Window):
#    type = "Frame"
#    def __init__(self, run, parent, title=u"", position=DefaultPosition, size=DefaultSize, style=wx.DEFAULT_FRAME_STYLE):
#        Window.__init__(self, run, parent, position=position, size=size, style=style)
#        self.title = title
#    def getConstructorData(self):
#        d = Window.getConstructorData(self)
#        d["title"] = self.title
#        return d
#
#class MiniFrame(Window):
#    type = "MiniFrame"
#    def __init__(self, run, parent, title=u"", position=DefaultPosition, size=DefaultSize, style=wx.DEFAULT_FRAME_STYLE):
#        Window.__init__(self, run, parent, position=position, size=size, style=style)
#        self.title = title
#    def getConstructorData(self):
#        d = Window.getConstructorData(self)
#        d["title"] = self.title
#        return d

class Frame(Window):
    """A Pyrope Frame uses a wxPython SizedFrame on the client-side. This is so, at least for simple cases, programmers won't
    need to deal with sizers so much. Varies wxPython settings are exposed through the properties argument to the constructor."""
    type = "Frame"
    _props = {"minimiseBox":wx.MINIMIZE_BOX,
             "maximiseBox":wx.MAXIMIZE_BOX,
             "resizeBorder":wx.RESIZE_BORDER,
             "systemMenu":wx.SYSTEM_MENU,
             "caption":wx.CAPTION,
             "closeBox":wx.CLOSE_BOX,
             "stayOnTop":wx.STAY_ON_TOP,
             "resizeable":wx.RESIZE_BORDER}
    def __init__(self, run, parent, title=u"", position=DefaultPosition, size=DefaultSize, sizerType="horizontal", 
                 minimiseBox=True, maximiseBox=True, closeBox=True, stayOnTop=True, systemMenu=True, resizeable=True):
        Window.__init__(self, run, parent, position=position, size=size)
        self.title = title
        self.sizerType = sizerType
        self.wxStyle = wx.DEFAULT_FRAME_STYLE
        self._addStyleToggle(minimiseBox, "minimiseBox")
        self._addStyleToggle(maximiseBox, "maximiseBox")
        self._addStyleToggle(closeBox, "closeBox")
        self._addStyleToggle(stayOnTop, "stayOnTop")
        self._addStyleToggle(systemMenu, "systemMenu")
        self.menuBar = None
    def _getConstructorData(self):
        d = Window._getConstructorData(self)
        d["title"] = self.title
        return d
    def _getOtherData(self):
        data = {"sizerType":self.sizerType}
        if self.menuBar:
            data["menuBar"] = self.menuBar.getConstructorDetails()
        else:
            data["menuBar"] = None
        return data

#class Dialog(Window):
#    type = "SizedDialog"
#    def __init__(self, run, parent, title=u"", position=DefaultPosition, size=DefaultSize):
#        Window.__init__(self, run, parent, position=position, size=size)
#        self.title = title
#    def _getConstructorData(self):
#        d = Window._getConstructorData(self)
#        d["title"] = self.title
#        return d
#    def showModal(self):
#        return self.callRemote("ShowModal")
#pb.setUnjellyableForClass(Dialog, Dialog)
#
#class MessageDialog(Window):
#    type = "MessageDialog"
#    def __init__(self, run, parent, message, caption=u"Message Box", position=DefaultPosition):
#        Window.__init__(self, run, parent, position=position)
#        self.caption = caption
#        self.message = message
#    def _getConstructorData(self):
#        d = Window._getConstructorData(self)
#        d["caption"] = self.caption
#        d["message"] = self.message
#        #no size for message box
#        del d["size"]
#        return d
#    def showModal(self):
#        return self.callRemote("ShowModal")
#pb.setUnjellyableForClass(MessageDialog, MessageDialog)

##########
## Panel #
##########
class Panel(Window):
    type = "Panel"
    def __init__(self, run, parent, position=DefaultPosition, size=DefaultSize, sizerType="vertical"):
        Window.__init__(self, run, parent, position=position, size=size)
        self.sizerType = sizerType
    def _getOtherData(self):
        return {"sizerType":self.sizerType}

############
## Widgets #
############

class TextBox(Window):
    type = "TextBox"
    _props = {"multiline":wx.TE_MULTILINE,
              "readonly":wx.TE_READONLY,
              "password":wx.TE_PASSWORD,
              "left":wx.TE_LEFT,
              "centre":wx.TE_CENTRE,
              "right":wx.TE_RIGHT,
              }
    def __init__(self, run, parent, value=u"", position=DefaultPosition, size=DefaultSize,
                 justification="left", multiline=False, readonly=False, password=False):
        Window.__init__(self, run, parent, position=position, size=size)
        self.value = value
        self._addStyleVal(multiline, "multiline")
        self._addStyleVal(readonly, "readonly")
        self._addStyleVal(password, "password")
        self._addStyleVal(justification == "left", "left")
        self._addStyleVal(justification == "centre", "centre")
        self._addStyleVal(justification == "right", "right")
    def _getConstructorData(self):
        d = Window._getConstructorData(self)
        d["value"] = self.value
        return d
    def setData(self, data):
        self.value = data
    def getData(self):
        return self.value
#    def handleEvent(self, event):
#        #TODO: check the event type, handle accordingly, throw exceptions if it can't handle it
#        self.value = event.data
#    def updateData(self, data):
#        #TODO: check the event type, handle accordingly, throw exceptions if it can't handle it
#        self.value = data
class Label(Window):
    type = "Label"
    _props = {"left":wx.ALIGN_LEFT,
              "centre":wx.ALIGN_CENTRE,
              "right":wx.ALIGN_RIGHT}
    def __init__(self, run, parent, value=u"", position=DefaultPosition, size=DefaultSize,
                 justification="left"):
        Window.__init__(self, run, parent, position=position, size=size)
        self.label = value
        self._addStyleVal(justification == "left", "left")
        self._addStyleVal(justification == "centre", "centre")
        self._addStyleVal(justification == "right", "right")
    def _getConstructorData(self):
        d = Window._getConstructorData(self)
        d["label"] = self.label
        return d
    def setData(self, data):
        self.label = data
    def getData(self):
        return self.label
#    def setValue(self, label):
#        #set the local background colour
#        self.label = label
#        #set remote
#        return self.callRemote("SetLabel", label)
#    def handleEvent(self, event):
#        self.label = event.data

class Button(Window):
    type = "Button"
    def __init__(self, run, parent, value=u"",
                 default=True):
        Window.__init__(self, run, parent)
        self.label = value
        self.default = default
    def _getConstructorData(self):
        d = Window._getConstructorData(self)
        d["label"] = self.label
        return d
    def _getOtherData(self):
        return{"default":self.default}

class Choice(Window):
    type = "Choice"
    _props = {"sortAlphabetically":wx.CB_SORT}
    def __init__(self, run, parent, choices=[], 
                 sortAlphabetically=False):
        Window.__init__(self, run, parent)
        self.choices = choices
        self._addStyleVal(sortAlphabetically, "sortAlphabetically")
        self.selectedIndex = 0
    def _getConstructorData(self):
        d = Window._getConstructorData(self)
        d["choices"] = self.choices
        return d
    def setData(self, data):
        self.selectedIndex = data
    def getData(self):
        return self.choices

class ListBox(Window):
    type = "ListBox"
    _props = {"sortAlphabetically":wx.LB_SORT,
              "multipleSelection":wx.LB_MULTIPLE}
    def __init__(self, run, parent, choices=[], 
                 multipleSelection=False, sortAlphabetically=False):
        Window.__init__(self, run, parent)
        self.choices = choices
        self._addStyleVal(sortAlphabetically, "sortAlphabetically")
        self._addStyleVal(multipleSelection, "multipleSelection")
    def _getConstructorData(self):
        d = Window._getConstructorData(self)
        d["choices"] = self.choices
        return d
    def setData(self, data):
        self.selectedIndex = data
    def getData(self):
        return self.choices

class CheckListBox(ListBox):
    type = "CheckListBox"

class CheckBox(Window):
    type = "CheckBox"
    _props = {"threeState":wx.CHK_3STATE,
              "userCanSelectThirdState":wx.CHK_ALLOW_3RD_STATE_FOR_USER,
              "alignRight":wx.ALIGN_RIGHT}
    def __init__(self, run, parent, label=u"", position=DefaultPosition, size=DefaultSize,
                 threeState=False, userCanSelectThirdState=False, alignRight=False):
        Window.__init__(self, run, parent, position=position, size=size)
        self.label = label
        self._addStyleVal(threeState, "threeState")
        self._addStyleVal(userCanSelectThirdState, "userCanSelectThirdState")
        self._addStyleVal(alignRight, "alignRight")
    def _getConstructorData(self):
        d = Window._getConstructorData(self)
        d["label"] = self.label
        return d

class Gauge(Window):
    type = "Gauge"
    _props = {"horizontal":wx.GA_HORIZONTAL,
              "vertical":wx.GA_VERTICAL}
    def __init__(self, run, parent, range=100, position=DefaultPosition, size=DefaultSize,
                 value=0, alignment="horizontal"):
        Window.__init__(self, run, parent, position=position, size=size)
        self.range = range
        self.value = value
        self._addStyleVal(alignment == "horizontal", "horizontal")
        self._addStyleVal(alignment == "vertical", "vertical")
    def _getConstructorData(self):
        d = Window._getConstructorData(self)
        d["range"] = self.range
        return d
    def _getOtherData(self):
        return {"value":self.value}

class Slider(Window):
    type = "Slider"
    _props = {"horizontal":wx.SL_HORIZONTAL,
              "vertical":wx.SL_VERTICAL,
              "displayTicks":wx.SL_AUTOTICKS,
              "displayLabels":wx.SL_LABELS,
              "left":wx.SL_LEFT,
              "right":wx.SL_RIGHT,
              "top":wx.SL_TOP,
              "bottom":wx.SL_BOTTOM}
    def __init__(self, run, parent, minValue=0, maxValue=100, position=DefaultPosition, size=DefaultSize,
                 alignment="horizontal", displayLabels=False, displayTicks=False, tickPosition="bottom"):
        Window.__init__(self, run, parent, position=position, size=size)
        self.minValue = minValue
        self.maxValue = maxValue
        self._addStyleVal(displayLabels, "displayLabels")
        self._addStyleVal(displayTicks, "displayTicks")
        self._addStyleVal(alignment == "horizontal", "horizontal")
        self._addStyleVal(alignment == "vertical", "vertical")
        self._addStyleVal(tickPosition == "bottom", "bottom")
        self._addStyleVal(tickPosition == "top", "top")
        self._addStyleVal(tickPosition == "left", "left")
        self._addStyleVal(tickPosition == "right", "right")        
    def _getConstructorData(self):
        d = Window._getConstructorData(self)
        d["minValue"] = self.minValue
        d["maxValue"] = self.maxValue
        return d

class Spinner(Window):
    type = "Spinner"
    _props = {"wrap":wx.SP_WRAP}
    def __init__(self, run, parent, value=u"0", range=(0,10), 
                 wrap=False):
        Window.__init__(self, run, parent)
        self.value = value
        self.range = range
        self._addStyleVal(wrap, "wrap")
    def _getConstructorData(self):
        d = Window._getConstructorData(self)
        d["value"] = self.value
        return d
    def _getOtherData(self):
        return {"range":self.range}

class RadioBox(Window):
    type = "RadioBox"
    _props = {"rows":wx.RA_SPECIFY_ROWS,
              "cols":wx.RA_SPECIFY_COLS}
    def __init__(self, run, parent, label=u"", choices=[], cols=0, rows=0):
        Window.__init__(self, run, parent)
        self.label = label
        self.choices = choices
        #if rows=0, assume cols is used:
        self.cols = cols
        self.rows = rows
        #default is cols, so no need to check for that
        if rows:
            self._addStyleVal(rows, "rows")
    def _getConstructorData(self):
        d = Window._getConstructorData(self)
        d["label"] = self.label
        d["choices"] = self.choices
        if not self.rows:
            d["majorDimension"] = self.cols
        else:
            d["majorDimension"] = self.rows
        return d

class Box(Window):
    type = "Box"
    def __init__(self, run, parent, label=u"", position=DefaultPosition, size=DefaultSize):
        Window.__init__(self, run, parent, position=position, size=size)
        self.label = label
    def _getConstructorData(self):
        d = Window._getConstructorData(self)
        d["label"] = self.label
        return d

class Line(Window):
    type = "Line"
    _props = {"horizontal":wx.LI_HORIZONTAL,
              "vertical":wx.LI_VERTICAL}
    def __init__(self, run, parent, position=DefaultPosition, size=DefaultSize,
                 orientation="horizontal"):
        Window.__init__(self, run, parent, position=position, size=size)
        self._addStyleVal(orientation == "horizontal", "horizontal")
        self._addStyleVal(orientation == "vertical", "vertical")
        

############
#   Menu   #
############
#XXX: this menubar stuff is implemented poorly!
class MenuBar(Window):
    type = "MenuBar"
    def __init__(self, run):
        Window.__init__(self, run, parent=None)
        self.menus = []
        self.itemHandlers = {}
        self.form = None
    def addMenu(self, menu):
        self.menus.append(menu)
    def bind(self, item, fn):
        self.itemHandlers[item.id] = fn
    def _getConstructorData(self):
        return {}
    def _getOtherData(self):
        return {"form":self.form, "menus":self.menus}
    def remote_menuItemSelected(self, id):
        if self.itemHandlers.has_key(id):
            self.itemHandlers[id]()
class Menu(pb.Copyable, pb.RemoteCopy):
    def __init__(self, title):
        self.title = title
        self.items = []
    def addItem(self, item):
        self.items.append(item)
pb.setUnjellyableForClass(Menu, Menu)

class MenuItem(pb.Copyable, pb.RemoteCopy):
    #XXX:burdens user from setting IDs, but is a hack!
    #id = 100
    def __init__(self, text, help=u""):
        #self.id = MenuItem.id = MenuItem.id+1
#        self.id = id
        #another hack!
        self.id = wx.NewId()
        self.text = text
        self.help = help
pb.setUnjellyableForClass(MenuItem, MenuItem)

