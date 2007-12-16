###########
# Defaults
###########
import wx

#values of -1, (-1, -1) etc. are usually defaults in wxWidgets
DefaultPosition = DefaultSize = (-1,-1)

##includes constants for the following (10 entries per line)
##wxWindow, wxFrame
#BorderSimple, BorderDouble, BorderSunken, BorderRaised, BorderTheme, BorderNone, TransparentWindow, TabTraversal, WantsChars, NoFullRepaintOnResize, \
#VScroll, HScroll, AlwaysShowScrollBars, ClipChildren, FullRepaintOnResize, Horizontal, Vertical,  Both, CentreOnScreen, DefaultFrameStyle, \
#Iconise, Caption, Minimise, MinimiseBox, Maximise, MaximiseBox, CloseBox, StayOnTop, SystemMenu, ResizeBorder, \
#FrameToolWindow, FrameNoTaskbar, FrameFloatOnParent, FrameExContextHelp, FrameShaped, FrameMetal, Caption, DefaultDialogStyle, ResizeBorder, ThickFrame, \
#No3D, DialogNoParent, DialogExContextHelp, DialogExMetal, Ok, Cancel, YesNo, YesDefault, NoDefault, IconExclamation, \
#IconHand, IconError, IconQuestion,  = range(44)
##
###maps Pyrope constants to wxWidgets constants
#constants = {BorderSimple:wx.BORDER_SIMPLE, BorderDouble:wx.BORDER_DOUBLE, BorderSunken:wx.BORDER_SUNKEN, BorderRaised:wx.BORDER_RAISED, BorderTheme:wx.BORDER_THEME, 
#             BorderNone:wx.BORDER_NONE, TransparentWindow:wx.TRANSPARENT_WINDOW, TabTraversal:wx.TAB_TRAVERSAL, WantsChars:wx.WANTS_CHARS, 
#             NoFullRepaintOnResize:wx.NO_FULL_REPAINT_ON_RESIZE, VScroll:wx.VSCROLL, HScroll:wx.HSCROLL, AlwaysShowScrollBars:wx.ALWAYS_SHOW_SB, 
#             ClipChildren:wx.CLIP_CHILDREN, FullRepaintOnResize:wx.FULL_REPAINT_ON_RESIZE, Horizontal:wx.HORIZONTAL, Vertical:wx.VERTICAL, Both:wx.BOTH, 
#             CentreOnScreen:wx.CENTRE_ON_SCREEN, DefaultFrameStyle:wx.DEFAULT_FRAME_STYLE, Iconise:wx.ICONIZE, Caption:wx.CAPTION, Minimise:wx.MINIMIZE,
#             MinimiseBox:wx.MINIMIZE_BOX, Maximise:wx.MAXIMIZE, MaximiseBox:wx.MAXIMIZE_BOX,CloseBox:wx.CLOSE_BOX, StayOnTop:wx.STAY_ON_TOP, SystemMenu:wx.SYSTEM_MENU, ResizeBorder:wx.RESIZE_BORDER,
#             FrameToolWindow:wx.FRAME_TOOL_WINDOW, FrameNoTaskbar:wx.FRAME_NO_TASKBAR, FrameFloatOnParent:wx.FRAME_FLOAT_ON_PARENT, FrameExContextHelp:wx.FRAME_EX_CONTEXTHELP, 
#             FrameShaped:wx.FRAME_SHAPED, FrameMetal:wx.FRAME_EX_METAL, Caption:wx.CAPTION, DefaultDialogStyle:wx.DEFAULT_DIALOG_STYLE, ResizeBorder:wx.RESIZE_BORDER, 
#             ThickFrame:wx.THICK_FRAME, No3D:wx.NO_3D, DialogNoParent:wx.DIALOG_NO_PARENT, DialogExContextHelp:wx.DIALOG_EX_CONTEXTHELP, DialogExMetal:wx.DIALOG_EX_METAL}
#

#EventClose, EventText, EventButton = range(3)
#events = {EventClose:wx.EVT_CLOSE, EventText:wx.EVT_TEXT, EventButton:wx.EVT_BUTTON}
