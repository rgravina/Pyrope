"""The Local (i.e. usually server-side) model."""
import wx
from zope.interface import implements, Interface, Attribute
from twisted.spread import pb
from twisted.python import log
from twisted.internet.defer import Deferred, inlineCallbacks
from pyrope.model.shared import *
from pyrope.model.remote import *
from pyrope.model.events import *
from pyrope.errors import RemoteResourceNotCreatedException
from PIL import Image as PILImage

class IApplication(Interface):
    """A Pyrope application"""
    def start(self, handler):
        """Start up the application"""

class RunningApplication(object):
    """Represents an instance of a running application.
    At this stage there are no methods, it just acts as a parameter object."""
    def __init__(self, app, perspective, handler):
        self.app = app                     #application object
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
        run = RunningApplication(self, perspective, handler)
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
        
class PyropeWidget(pb.Referenceable, object):
    """Base class for Pyrope widgets. Sublcasses object because we want to use properties (new style classes only)."""
    type = "PyropeWidget"
    def __init__(self, run):
        self.run = run
        run.widgets.append(self)
        #the remote reference will be set when the client calls remote_handleEvent
        self.remote = None
        #for event handling
        self.eventHandlers = {}

    #creating and calling remote side
    @inlineCallbacks
    def createRemote(self):
        #creates remote widget, and gets a pb.RemoteReference to it's client-side proxy
        self.remote = yield self.run.handler.callRemote("createWidget", self.getConstructorDetails())
    def callRemote(self, functName, *args):
        if self.remote:
            return self.remote.callRemote(functName, *args)
        else:
            raise RemoteResourceNotCreatedException, "You must call createRemote before calling this method"
    def remote_updateRemote(self, remote):
        """Called by client when remote handler for wxWidget is ready"""
        self.remote = remote


    #event handling
    def bind(self, event, handlerFunction):
        """Adds handlerFunction to event handler list for this event type."""
        #TODO: make a better API for event chaining and propagation        
        #create list of event handlers for this event if it doesn't exist already
        #otherwise, add the event to the list of handlers
        if not self.eventHandlers.has_key(event):
            self.eventHandlers[event] = []
        self.eventHandlers[event].append(handlerFunction)
    def remote_handleEvent(self, event, changeset=None):
        """Called by client when an event has been fired. Includes an event and changeset"""
        #apply changeset
        if changeset:
            changeset.apply()
        
        #TODO: make a better API for event chaining and propagation        
        #call event handler
        for handler in self.eventHandlers[event.eventType]:
            # handlers return True if they want event to propegate
            if not handler(event):
                break

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
#    def syncWithRemote(self):
#        def _done(data):
#            self.setData(data)
#        return self.callRemote("getData").addCallback(_done)
#    def syncWithLocal(self):
#        return self.callRemote("setData", self.getData())
    def clientToScreen(self, point):
        return self.callRemote("ClientToScreen", point)
    def hide(self):
        return self.callRemote("Hide")
    def show(self):
        return self.callRemote("Show")
    def centre(self, direction=wx.BOTH, centreOnScreen=False):
        return self.callRemote("Centre", direction, centreOnScreen)
    def close(self):
        return self.callRemote("Close")
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

#def syncWithRemote(*args):
#    """Takes a list of Pyrope Widgets and calls syncWithRemote on each, and immediately returns a Deferred. When all widgets have successfully synced, the callback 
#    sequence is fired on the deferred."""
#    #list of completed widgets
#    doneList = []
#    d = Deferred()
#    def _done(result, widget):
#        doneList.append(widget)
#        if len(doneList) is len(args):
#            d.callback(True)
#    #call syncWithRemote on each widget
#    for widget in args:
#        widget.syncWithRemote().addCallback(_done, widget)
#    return d
#
#def syncWithLocal(*args):
#    """Takes a list of Pyrope Widgets and calls syncWithLocal on each, and immediately returns a Deferred. When all widgets have successfully synced, the callback 
#    sequence is fired on the deferred."""
#    #list of completed widgets
#    doneList = []
#    d = Deferred()
#    def _done(result, widget):
#        doneList.append(widget)
#        if len(doneList) is len(args):
#            d.callback(True)
#    #call syncWithLocal on each widget
#    for widget in args:
#        widget.syncWithLocal().addCallback(_done, widget)
#    return d
#
#def sync(run):
#    """Updates client based on server changset"""
#    print "syncing"
#    print run.changeset.changes

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
        self._addStyleToggle(resizeable, "resizeBorder")
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

class Dialog(Window):
    type = "Dialog"
    def __init__(self, run, parent, title=u"", position=DefaultPosition, size=DefaultSize):
        Window.__init__(self, run, parent, position=position, size=size)
        self.title = title
    def _getConstructorData(self):
        d = Window._getConstructorData(self)
        d["title"] = self.title
        return d
    def showModal(self):
        return self.callRemote("ShowModal")

class MessageDialog(Window):
    type = "MessageDialog"
    def __init__(self, run, parent, message, caption=u"Message Box", position=DefaultPosition):
        Window.__init__(self, run, parent, position=position)
        self.caption = caption
        self.message = message
    def _getConstructorData(self):
        d = Window._getConstructorData(self)
        d["caption"] = self.caption
        d["message"] = self.message
        #no size for message box
        del d["size"]
        return d
    def showModal(self):
        return self.callRemote("ShowModal")

class TextEntryDialog(Window):
    type = "TextEntryDialog"
    _props = {"cancelButton":wx.CANCEL}
    def __init__(self, run, parent, message, caption=u"Please enter text", defaultValue="", position=DefaultPosition,
                 cancelButton=False):
        Window.__init__(self, run, parent, position=position)
        self.caption = caption
        self.message = message
        self.defaultValue = defaultValue
        #different from wxPython defaults
        self.wxStyle = wx.OK | wx.CENTRE
        self._addStyleVal(cancelButton, "cancelButton")
    def _getConstructorData(self):
        d = Window._getConstructorData(self)
        d["caption"] = self.caption
        d["message"] = self.message
        d["defaultValue"] = self.defaultValue
        #no size for message box
        del d["size"]
        return d
    def showModalAndGetValue(self):
        return self.callRemote("showModalAndGetValue")

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
              "processEnter":wx.TE_PROCESS_ENTER}
    def __init__(self, run, parent, value=u"", position=DefaultPosition, size=DefaultSize,
                 justification="left", multiline=False, readonly=False, password=False, processEnter=False):
        Window.__init__(self, run, parent, position=position, size=size)
        self._value = value
        self._addStyleVal(multiline, "multiline")
        self._addStyleVal(readonly, "readonly")
        self._addStyleVal(password, "password")
        self._addStyleVal(justification == "left", "left")
        self._addStyleVal(justification == "centre", "centre")
        self._addStyleVal(justification == "right", "right")
        self._addStyleVal(processEnter, "processEnter")
    def _getConstructorData(self):
        d = Window._getConstructorData(self)
        d["value"] = self._value
        return d

    def _getValue(self):
        return self._value
    def _setValue(self, value):
        self._value = value
        return self.callRemote("setValue", value)
    value = property(_getValue, _setValue)
    
#    def setData(self, data):
#        self.value = data
#    def getData(self):
#        return self.value
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
        self._label = value
        self._addStyleVal(justification == "left", "left")
        self._addStyleVal(justification == "centre", "centre")
        self._addStyleVal(justification == "right", "right")
    def _getConstructorData(self):
        d = Window._getConstructorData(self)
        d["label"] = self._label
        return d

    def _getValue(self):
        return self._label
    def _setValue(self, value):
        self._label = value
        return self.callRemote("setLabel", value)
    label = property(_getValue, _setValue)

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

class BitmapButton(Window):
    type = "BitmapButton"
    def __init__(self, run, parent, image,
                 default=True):
        Window.__init__(self, run, parent)
        self.image = image
        self.default = default
    def _getOtherData(self):
        d = Window._getConstructorData(self)
        d["image"] = self.image.data
        d["default"] = self.default
        return d

class ControlWithItemsMixin:
    def _getSelectedIndex(self):
        return self._selectedIndex
    def _setSelectedIndex(self, value):
        self._selectedIndex = value
        return self.callRemote("setSelectedIndex", value)
    selectedIndex = property(_getSelectedIndex, _setSelectedIndex)

    def _getChoices(self):
        return self._choices
    def _setChoices(self, value):
        self._choices = value
        return self.callRemote("setChoices", value)
    choices = property(_getChoices, _setChoices)

    def setChoice(self, index, value):
        self._choices[index] = value
        return self.callRemote("setChoice", index, value)
    
    def append(self, value):
        self._choices.append(value)
        return self.callRemote("append", value)

    def delete(self, index):
        del self._choices[index]
        return self.callRemote("delete", index)

class Choice(Window, ControlWithItemsMixin):
    type = "Choice"
    _props = {"sortAlphabetically":wx.CB_SORT}
    def __init__(self, run, parent, choices=[], 
                 sortAlphabetically=False):
        Window.__init__(self, run, parent)
        self._selectedIndex = 0
        self._choices = choices
        self._addStyleVal(sortAlphabetically, "sortAlphabetically")
    def _getConstructorData(self):
        d = Window._getConstructorData(self)
        d["choices"] = self._choices
        return d

class ListBox(Window, ControlWithItemsMixin):
    type = "ListBox"
    _props = {"sortAlphabetically":wx.LB_SORT,
              "multipleSelection":wx.LB_MULTIPLE}
    def __init__(self, run, parent, choices=[], position=DefaultPosition, size=DefaultSize,
                 multipleSelection=False, sortAlphabetically=False):
        Window.__init__(self, run, parent, position=position, size=size)
        self._selectedIndex = None
        self._choices = choices
        self._addStyleVal(sortAlphabetically, "sortAlphabetically")
        self._addStyleVal(multipleSelection, "multipleSelection")
    def _getConstructorData(self):
        d = Window._getConstructorData(self)
        d["choices"] = self._choices
        return d


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
        

class Splitter(Window):
    type = "Splitter"
    _props = {"3d":wx.SP_3D,
              "border":wx.BORDER,
              "liveUpdate":wx.SP_LIVE_UPDATE}
    def __init__(self, run, parent, position=DefaultPosition, size=DefaultSize,
                 border=False, liveUpdate=False, mode="horizontal", minimumPaneSize=0):
        Window.__init__(self, run, parent, position=position, size=size)
        self._addStyleVal(border, "border")
        self._addStyleVal(liveUpdate, "liveUpdate")
        self.mode = mode
        self.minimumPaneSize = minimumPaneSize
    def _getOtherData(self):
        return {"mode":self.mode, "minimumPaneSize":self.minimumPaneSize}

############
#   Menu   #
############
#XXX: this menubar stuff is implemented poorly!
class MenuBar(Window):
    type = "MenuBar"
    def __init__(self, run, form):
        Window.__init__(self, run, parent=None)
        self.menus = []
        self.itemHandlers = {}
        self.form = form
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

class ToolBar(Window):
    type = "ToolBar"
    _props = {"horizontal":wx.TB_HORIZONTAL,
              "vertical":wx.TB_VERTICAL,
              "text":wx.TB_TEXT,
              "noicons":wx.TB_NOICONS,
              "notooltips":wx.TB_NO_TOOLTIPS,
              "bottom":wx.TB_BOTTOM,
              "right":wx.TB_RIGHT}
    def __init__(self, run, parent, position=DefaultPosition, size=DefaultSize,
                 orientation="horizontal", text=False, icons=True, tooltips=True, alignment="top"):
        Window.__init__(self, run, parent, position=position, size=size)
        self._addStyleVal(orientation == "horizontal", "horizontal")
        self._addStyleVal(orientation == "vertical", "vertical")
        self._addStyleVal(text, "text")
        self._addStyleVal(not icons, "noicons")
        self._addStyleVal(not tooltips, "notooltips")
        self._addStyleVal(alignment == "bottom", "bottom")
        self._addStyleVal(alignment == "right", "right")
        self.tools = []
#    def addWidget(self, widget):
#        self.children.append(widget)
    def addTool(self, label, image):
        self.tools.append((label, image.data))
    def _getOtherData(self):
        return {"tools":self.tools}

class StatusBar(Window):
    type = "StatusBar"
    def __init__(self, run, parent, fields={}):
        Window.__init__(self, run, parent)
        self._fields = fields    #index->text
    def _getConstructorData(self):
        return {"parent":self.parent}
    def _getOtherData(self):
        return {"fields":self._fields}

    def _getFields(self):
        return self._fields
    def _setFields(self, value):
        self._fields = value
        return self.callRemote("setFields", value)
    fields = property(_getFields, _setFields)
 
class Image(Window):
    type = "Image"
    def __init__(self, run, parent, path):
        Window.__init__(self, run, parent)
        self.image = open(path)
        self.data = self.image.read()
    def _getOtherData(self):
        return {"parent":self.parent, "data":self.data}

class Notebook(Window):
    type = "Notebook"
    _props = {"top":wx.NB_TOP,
              "left":wx.NB_LEFT,
              "right":wx.NB_RIGHT,
              "bottom":wx.NB_BOTTOM}
    def __init__(self, run, parent, position=DefaultPosition, size=DefaultSize,
                 tabPosition="top"):
        Window.__init__(self, run, parent, position=position, size=size)
        self.pages = []
        self._addStyleVal(tabPosition == "top", "top")
        self._addStyleVal(tabPosition == "bottom", "bottom")
        self._addStyleVal(tabPosition == "left", "left")
        self._addStyleVal(tabPosition == "right", "right")
    def addPage(self, title, page):
        self.pages.append((title, page))
    def _getOtherData(self):
        return {"pages":self.pages}
