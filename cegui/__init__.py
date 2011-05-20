################################################################################
#   CEED - A unified CEGUI editor
#   Copyright (C) 2011 Martin Preisler <preisler.m@gmail.com>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
################################################################################

from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtOpenGL import *

from OpenGL.GL import *

import ui.ceguidebuginfo

import os.path
import time
import math

import PyCEGUI
import PyCEGUIOpenGLRenderer

import resizable

#class CEGUIQtLogger(PyCEGUI.Logger):
#    """Redirects CEGUI log info to CEGUIWidgetInfo"""
#
#    # This is a separate class from CEGUIWidgetInfo because PySide and PyCEGUI
#    # don't like mixing base classes at all
#    
#    def __init__(self, widgetInfo):
#        super(CEGUIQtLogger, self).__init__()
#        
#        self.widgetInfo = widgetInfo
#        
#    def logEvent(self, message, level):
#        self.widgetInfo.logEvent(message, level)
#        
#    def setLogFilename(self, name, append):
#        pass

class DebugInfo(QDockWidget):
    """A debugging/info widget about the embedded CEGUI instance"""
    
    # This will allow us to view logs in Qt in the future
    
    def __init__(self, containerWidget):
        super(DebugInfo, self).__init__()
        
        self.setVisible(False)
        
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        
        self.containerWidget = containerWidget
        # update FPS and render time very second
        self.boxUpdateInterval = 1
        
        self.ui = ui.ceguidebuginfo.Ui_CEGUIWidgetInfo()
        self.ui.setupUi(self)
        
        self.currentFPSBox = self.findChild(QLineEdit, "currentFPSBox")
        self.currentRenderTimeBox = self.findChild(QLineEdit, "currentRenderTimeBox")
        
        self.errors = 0
        self.errorsBox = self.findChild(QLineEdit, "errorsBox")
        
        self.warnings = 0
        self.warningsBox = self.findChild(QLineEdit, "warningsBox")
        
        self.others = 0
        self.othersBox = self.findChild(QLineEdit, "othersBox")
        
    def logEvent(self, message, level):
        if level == PyCEGUI.LoggingLevel.Errors:
            self.errors += 1
            self.errorsBox.setText(str(self.errors))
            
        elif level == PyCEGUI.LoggingLevel.Warnings:
            self.warnings += 1
            self.warningsBox.setText(str(self.warnings))
        else:
            self.others += 1
            self.othersBox.setText(str(self.others))
        
        print message.c_str()

class GraphicsScene(QGraphicsScene):
    """A scene that draws CEGUI as it's background.
    
    Subclass this to be able to show Qt graphics items and widgets
    on top of the embedded CEGUI widget!
    
    Interaction is also supported
    """
    
    def __init__(self):
        super(GraphicsScene, self).__init__()
        
        self.initialised = False
        
        self.scenePadding = 100
        
        self.ceguiDisplaySize = PyCEGUI.Sizef(800, 600)
        self.fbo = None
        
    def setCEGUIDisplaySize(self, width, height, lazyUpdate = True):
        self.ceguiDisplaySize = PyCEGUI.Sizef(width, height)
        self.setSceneRect(QRectF(-self.scenePadding, -self.scenePadding,
                                 width + 2 * self.scenePadding, height + 2 * self.scenePadding))
        
        if not lazyUpdate:
            PyCEGUI.System.getSingleton().notifyDisplaySizeChanged(self.ceguiDisplaySize)
            
        self.fbo = None

    def initialise(self):
        self.setCEGUIDisplaySize(self.ceguiDisplaySize.d_width, self.ceguiDisplaySize.d_height)

    def drawBackground(self, painter, rect):
        """We override this and draw CEGUI instead of the whole background.
        
        Things to keep in mind: CEGUI sets it's own matrices so the view and scene size
        have to be exactly the same (in other words, QGraphicsView scrolling facilities
        won't work).
        
        The best way to work this around is to have a QScrollView and QGraphicsView inside
        it. This wraps the whole thing and scrolling works perfectly for the cost of some
        slight flicker.
        """
        
        # be robust, this is usually caused by recursive repainting
        if painter.paintEngine() is None:
            return
        
        painterType = painter.paintEngine().type()
        if painterType != QPaintEngine.OpenGL and painterType != QPaintEngine.OpenGL2:
            qWarning("cegui.GraphicsScene: drawBackground needs a "
                     "QGLWidget to be set as viewport on the "
                     "graphics view")
            
            return

        painter.beginNativePainting()
                
        containerWidget = self.views()[0].containerWidget
        containerWidget.ensureCEGUIIsInitialised()
        
        if not self.initialised:
            self.initialise()
            self.initialised = True
        
        if self.ceguiDisplaySize != PyCEGUI.System.getSingleton().getRenderer().getDisplaySize():
            PyCEGUI.System.getSingleton().notifyDisplaySizeChanged(self.ceguiDisplaySize)
        
        # signalRedraw is called to work around potential issues with dangling
        # references in the rendering code for some versions of CEGUI.
        system = PyCEGUI.System.getSingleton()
        system.signalRedraw()
        
        glClearColor(0.3, 0.3, 0.3, 1)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        # we have to render to FBO and then scale/translate that since CEGUI doesn't allow
        # scaling the whole rendering root directly
        
        # this makes sure the FBO is the correct size
        if not self.fbo:
            desiredSize = QSize(math.ceil(self.ceguiDisplaySize.d_width), math.ceil(self.ceguiDisplaySize.d_height))
            self.fbo = QGLFramebufferObject(desiredSize, GL_TEXTURE_2D)
            
        self.fbo.bind()
        
        glClearColor(0, 0, 0, 1)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        system.renderGUI()
        
        self.fbo.release()

        # the stretch and translation should be done automatically by QPainter at this point so just
        # this code will do
        glActiveTexture(GL_TEXTURE0)
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.fbo.texture())

        glBegin(GL_TRIANGLES)
        
        # top left
        glTexCoord2f(0, 1)
        glVertex3f(0, 0, 0)
        
        # top right
        glTexCoord2f(1, 1)
        glVertex3f(self.fbo.size().width(), 0, 0)
        
        # bottom right
        glTexCoord2f(1, 0)
        glVertex3f(self.fbo.size().width(), self.fbo.size().height(), 0)
        
        # bottom right
        glTexCoord2f(1, 0)
        glVertex3f(self.fbo.size().width(), self.fbo.size().height(), 0)
        
        # bottom left
        glTexCoord2f(0, 0)
        glVertex3f(0, self.fbo.size().height(), 0)
        
        # top left
        glTexCoord2f(0, 1)
        glVertex3f(0, 0, 0)
        system.signalRedraw()
        
        glEnd()
        
        painter.endNativePainting()
        
        # TODO: Fake time impulse for now
        system.injectTimePulse(1)
        
        # 10 msec after rendering is finished, we mark this as dirty to force a rerender
        # this seems to be a good compromise
        #QTimer.singleShot(10, self.update)
        
        self.update()
                
        self.views()[0].parent().getWidgetPreviewImage("TaharezLook/FrameWindow").save("text.png")

class GraphicsView(resizable.GraphicsView):
    """This is a final class, not suitable for subclassing. This views given scene
    using QGLWidget. It's designed to work with cegui.GraphicsScene derived classes.
    
    """
    
    def __init__(self, parent = None):
        super(GraphicsView, self).__init__(parent)
        
        # we use Qt designer to put this together so we will set it later, not via constructor
        self.containerWidget = None
        
        self.setViewport(QGLWidget())
        # OpenGL doesn't do partial redraws (it isn't practical anyways)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        
        self.injectInput = False
        # we might want mouse events
        self.setMouseTracking(True)
        # we might want key events
        self.setFocusPolicy(Qt.ClickFocus)

    def resizeEvent(self, event):
        # overridden to make sure scene's size is always kept in sync with view's size

        #if self.scene():
        #    if self.containerWidget.CEGUIInitialised:
        #        PyCEGUI.System.getSingleton().notifyDisplaySizeChanged(PyCEGUI.Sizef(event.size().width(), event.size().height()))
        #        
        #    self.scene().setSceneRect(QRect(QPoint(0, 0), event.size()))
        
        super(GraphicsView, self).resizeEvent(event)
    
    def mouseMoveEvent(self, event):
        handled = False
        
        if self.injectInput:
            point = self.mapToScene(QPoint(event.x(), event.y()))
            handled = PyCEGUI.System.getSingleton().injectMousePosition(point.x(), point.y())
        
        if not handled:    
            super(GraphicsView, self).mouseMoveEvent(event)
        
    def translateQtMouseButton(self, button):
        ret = None
        
        if button == Qt.LeftButton:
            ret = PyCEGUI.MouseButton.LeftButton
        if button == Qt.RightButton:
            ret = PyCEGUI.MouseButton.RightButton
            
        return ret
    
    def mousePressEvent(self, event):
        # FIXME: Somehow, if you drag on the Live preview in layout editing on Linux,
        #        it drag moves the whole window
        
        handled = False
        
        if self.injectInput:
            button = self.translateQtMouseButton(event.button())

            if button is not None:
                handled = PyCEGUI.System.getSingleton().injectMouseButtonDown(button)
                
        if not handled:
            super(GraphicsView, self).mousePressEvent(event)
        
    def mouseReleaseEvent(self, event):
        handled = False
        
        if self.injectInput:
            button = self.translateQtMouseButton(event.button())
            
            if button is not None:
                handled = PyCEGUI.System.getSingleton().injectMouseButtonUp(button)
                
        if not handled:
            super(GraphicsView, self).mouseReleaseEvent(event)
    
    def translateQtKeyboardButton(self, button):
        # Shame this isn't standardised :-/ Was a pain to write down
        
        if button == Qt.Key_Escape:
            return PyCEGUI.Key.Escape
        elif button == Qt.Key_Tab:
            return PyCEGUI.Key.Tab
        # missing Backtab
        elif button == Qt.Key_Backspace:
            return PyCEGUI.Key.Backspace
        elif button in [Qt.Key_Return, Qt.Key_Enter]:
            return PyCEGUI.Key.Return
        elif button == Qt.Key_Insert:
            return PyCEGUI.Key.Insert
        elif button == Qt.Key_Delete:
            return PyCEGUI.Key.Delete
        elif button == Qt.Key_Pause:
            return PyCEGUI.Key.Pause
        # missing Print
        elif button == Qt.Key_SysReq:
            return PyCEGUI.Key.SysRq
        elif button == Qt.Key_Home:
            return PyCEGUI.Key.Home
        elif button == Qt.Key_End:
            return PyCEGUI.Key.End
        elif button == Qt.Key_Left:
            return PyCEGUI.Key.ArrowLeft
        elif button == Qt.Key_Up:
            return PyCEGUI.Key.ArrowUp
        elif button == Qt.Key_Right:
            return PyCEGUI.Key.ArrowRight
        elif button == Qt.Key_Down:
            return PyCEGUI.Key.ArrowDownGraphicsScene
        elif button == Qt.Key_PageUp:
            return PyCEGUI.Key.PageUp
        elif button == Qt.Key_PageDown:
            return PyCEGUI.Key.PageDown
        elif button == Qt.Key_Shift:
            return PyCEGUI.Key.LeftShift
        elif button == Qt.Key_Control:
            return PyCEGUI.Key.LeftControl
        elif button == Qt.Key_Meta:
            return PyCEGUI.Key.LeftWindows
        elif button == Qt.Key_Alt:
            return PyCEGUI.Key.LeftAlt
        # missing AltGr
        # missing CapsLock
        # missing NumLock
        # missing ScrollLock
        elif button == Qt.Key_F1:
            return PyCEGUI.Key.F1
        elif button == Qt.Key_F2:
            return PyCEGUI.Key.F2
        elif button == Qt.Key_F3:
            return PyCEGUI.Key.F3
        elif button == Qt.Key_F4:
            return PyCEGUI.Key.F4
        elif button == Qt.Key_F5:
            return PyCEGUI.Key.F5
        elif button == Qt.Key_F6:
            return PyCEGUI.Key.F6
        elif button == Qt.Key_F7:
            return PyCEGUI.Key.F7
        elif button == Qt.Key_F8:
            return PyCEGUI.Key.F8
        elif button == Qt.Key_F9:
            return PyCEGUI.Key.F9
        elif button == Qt.Key_F10:
            return PyCEGUI.Key.F10
        elif button == Qt.Key_F11:
            return PyCEGUI.Key.F11
        elif button == Qt.Key_F12:
            return PyCEGUI.Key.F12
        elif button == Qt.Key_F13:
            return PyCEGUI.Key.F13
        elif button == Qt.Key_F14:
            return PyCEGUI.Key.F14
        elif button == Qt.Key_F15:
            return PyCEGUI.Key.F15
        # missing F16 - F35
        # Qt::Key_Super_L    0x01000053     
        # Qt::Key_Super_R    0x01000054     
        # Qt::Key_Menu    0x01000055     
        # Qt::Key_Hyper_L    0x01000056     
        # Qt::Key_Hyper_R    0x01000057     
        # Qt::Key_Help    0x01000058     
        # Qt::Key_Direction_L    0x01000059     
        # Qt::Key_Direction_R    0x01000060
        elif button == Qt.Key_Space:
            return PyCEGUI.Key.Space
        # missing Exclam
        # Qt::Key_QuoteDbl    0x22     
        # Qt::Key_NumberSign    0x23     
        # Qt::Key_Dollar    0x24     
        # Qt::Key_Percent    0x25     
        # Qt::Key_Ampersand    0x26     
        elif button == Qt.Key_Apostrophe:
            return PyCEGUI.Key.Apostrophe     
        # Qt::Key_ParenLeft    0x28     
        # Qt::Key_ParenRight    0x29
        # Qt::Key_Asterisk    0x2a     
        # Qt::Key_Plus    0x2b
        elif button == Qt.Key_Comma:
            return PyCEGUI.Key.Comma
        elif button == Qt.Key_Minus:
            return PyCEGUI.Key.Minus
        elif button == Qt.Key_Period:
            return PyCEGUI.Key.Period
        elif button == Qt.Key_Slash:
            return PyCEGUI.Key.Slash
        elif button == Qt.Key_0:
            return PyCEGUI.Key.Zero
        elif button == Qt.Key_1:
            return PyCEGUI.Key.One
        elif button == Qt.Key_2:
            return PyCEGUI.Key.Two
        elif button == Qt.Key_3:
            return PyCEGUI.Key.Three
        elif button == Qt.Key_4:
            return PyCEGUI.Key.Four
        elif button == Qt.Key_5:
            return PyCEGUI.Key.Five
        elif button == Qt.Key_6:
            return PyCEGUI.Key.Six
        elif button == Qt.Key_7:
            return PyCEGUI.Key.Seven
        elif button == Qt.Key_8:
            return PyCEGUI.Key.Eight
        elif button == Qt.Key_9:
            return PyCEGUI.Key.Nine
        elif button == Qt.Key_Colon:
            return PyCEGUI.Key.Colon
        elif button == Qt.Key_Semicolon:
            return PyCEGUI.Key.Semicolon
        # missing Key_Less
        elif button == Qt.Key_Equal:
            return PyCEGUI.Key.Equals
        # missing Key_Greater
        # missing Key_Question
        elif button == Qt.Key_At:
            return PyCEGUI.Key.At
        elif button == Qt.Key_A:
            return PyCEGUI.Key.A
        elif button == Qt.Key_B:
            return PyCEGUI.Key.B
        elif button == Qt.Key_C:
            return PyCEGUI.Key.C
        elif button == Qt.Key_D:
            return PyCEGUI.Key.D
        elif button == Qt.Key_E:
            return PyCEGUI.Key.E
        elif button == Qt.Key_F:
            return PyCEGUI.Key.F
        elif button == Qt.Key_G:
            return PyCEGUI.Key.G
        elif button == Qt.Key_H:
            return PyCEGUI.Key.H
        elif button == Qt.Key_I:
            return PyCEGUI.Key.I
        elif button == Qt.Key_J:
            return PyCEGUI.Key.J
        elif button == Qt.Key_K:
            return PyCEGUI.Key.K
        elif button == Qt.Key_L:
            return PyCEGUI.Key.L
        elif button == Qt.Key_M:
            return PyCEGUI.Key.M
        elif button == Qt.Key_N:
            return PyCEGUI.Key.N
        elif button == Qt.Key_O:
            return PyCEGUI.Key.O
        elif button == Qt.Key_P:
            return PyCEGUI.Key.P
        elif button == Qt.Key_Q:
            return PyCEGUI.Key.Q
        elif button == Qt.Key_R:
            return PyCEGUI.Key.R
        elif button == Qt.Key_S:
            return PyCEGUI.Key.S
        elif button == Qt.Key_T:
            return PyCEGUI.Key.T
        elif button == Qt.Key_U:
            return PyCEGUI.Key.U
        elif button == Qt.Key_V:
            return PyCEGUI.Key.V
        elif button == Qt.Key_W:
            return PyCEGUI.Key.W
        elif button == Qt.Key_X:
            return PyCEGUI.Key.X
        elif button == Qt.Key_Y:
            return PyCEGUI.Key.Y
        elif button == Qt.Key_Z:
            return PyCEGUI.Key.Z
        
        # The rest are weird keys I refuse to type here
        
    def keyPressEvent(self, event):
        handled = False
        
        if self.injectInput:
            button = self.translateQtKeyboardButton(event.key())
            
            if button is not None:
                handled = PyCEGUI.System.getSingleton().injectKeyDown(button)
                
            char = event.text()
            if len(char) > 0:
                handled = handled or PyCEGUI.System.getSingleton().injectChar(ord(char[0]))
                
        if not handled:
            super(GraphicsView, self).keyPressEvent(event)
    
    def keyReleaseEvent(self, event):
        handled = False
        
        if self.injectInput:
            button = self.translateQtKeyboardButton(event.key())
            
            if button is not None:
                handled = PyCEGUI.System.getSingleton().injectKeyUp(button)
                
        if not handled:
            super(GraphicsView, self).keyPressEvent(event)

# we import here to avoid circular dependencies (GraphicsView has to be defined at this point)
import ui.ceguicontainerwidget

class ContainerWidget(QWidget):
    """
    This widget is what you should use (alongside your GraphicsScene derived class) to
    put CEGUI inside parts of the editor.
    
    Provides resolution changes, auto expanding and debug widget
    """
    
    def __init__(self, mainWindow):
        super(ContainerWidget, self).__init__()
        
        self.CEGUIInitialised = False
        
        self.ui = ui.ceguicontainerwidget.Ui_CEGUIContainerWidget()
        self.ui.setupUi(self)
        
        self.currentParentWidget = None

        self.debugInfo = DebugInfo(self)
        self.view = self.findChild(GraphicsView, "view")
        self.view.setBackgroundRole(QPalette.Dark)
        self.view.containerWidget = self
        
        self.autoExpand = self.findChild(QCheckBox, "autoExpand")
        self.autoExpand.stateChanged.connect(self.slot_autoExpandChanged)
        self.resolutionBox = self.findChild(QComboBox, "resolutionBox")
        self.resolutionBox.editTextChanged.connect(self.slot_resolutionBoxChanged)
        
        self.debugInfoButton = self.findChild(QPushButton, "debugInfoButton")
        self.debugInfoButton.clicked.connect(self.slot_debugInfoButton)
    
    def ensureCEGUIIsInitialised(self):
        if not self.CEGUIInitialised:
            self.makeGLContextCurrent()
            
            PyCEGUIOpenGLRenderer.OpenGLRenderer.bootstrapSystem(PyCEGUIOpenGLRenderer.OpenGLRenderer.TTT_NONE)
            self.CEGUIInitialised = True

            self.setDefaultResourceGroups()
    
    def enableInput(self):
        self.view.injectInput = True
        
    def disableInput(self):
        self.view.injectInput = False
         
    def setResourceGroupDirectory(self, resourceGroup, absolutePath):
        self.ensureCEGUIIsInitialised()
        
        rp = PyCEGUI.System.getSingleton().getResourceProvider()
 
        rp.setResourceGroupDirectory(resourceGroup, absolutePath)
    
    def setDefaultResourceGroups(self):
        self.ensureCEGUIIsInitialised()
        
        # reasonable default directories
        defaultBaseDirectory = os.path.join(os.path.curdir, "datafiles")
        
        self.setResourceGroupDirectory("imagesets",
                                       os.path.join(defaultBaseDirectory, "imagesets"))
        self.setResourceGroupDirectory("fonts",
                                       os.path.join(defaultBaseDirectory, "fonts"))
        self.setResourceGroupDirectory("schemes",
                                       os.path.join(defaultBaseDirectory, "schemes"))
        self.setResourceGroupDirectory("looknfeels",
                                       os.path.join(defaultBaseDirectory, "looknfeel"))
        self.setResourceGroupDirectory("layouts",
                                       os.path.join(defaultBaseDirectory, "layouts"))
        
        # all this will never be set to anything else again
        PyCEGUI.ImageManager.setImagesetDefaultResourceGroup("imagesets")
        PyCEGUI.Font.setDefaultResourceGroup("fonts")
        PyCEGUI.Scheme.setDefaultResourceGroup("schemes")
        PyCEGUI.WidgetLookManager.setDefaultResourceGroup("looknfeels")
        PyCEGUI.WindowManager.setDefaultResourceGroup("layouts")
        
        parser = PyCEGUI.System.getSingleton().getXMLParser()
        if parser.isPropertyPresent("SchemaDefaultResourceGroup"):
            parser.setProperty("SchemaDefaultResourceGroup", "schemas")
        
    def syncToProject(self, project):
        progress = QProgressDialog(self)
        progress.setWindowModality(Qt.WindowModal)
        progress.setWindowTitle("Synchronising embedded CEGUI with the project")
        progress.setCancelButton(None)
        progress.resize(400, 100)
        progress.show()
        
        self.ensureCEGUIIsInitialised()
        self.makeGLContextCurrent()
        
        schemes = []
        absoluteSchemesPath = project.getAbsolutePathOf(project.schemesPath)
        if os.path.exists(absoluteSchemesPath):
            for file in os.listdir(absoluteSchemesPath):
                if file.endswith(".scheme"):
                    schemes.append(file)
        else:
            # TODO: warning perhaps?
            #       with a dialog to let user immediately remedy the situation before loading continues
            pass

        progress.setMinimum(0)
        progress.setMaximum(3 + len(schemes))
        
        progress.setLabelText("Purging all resources...")
        progress.setValue(0)
        
        # destroy all previous resources (if any)
        PyCEGUI.WindowManager.getSingleton().destroyAllWindows()
        PyCEGUI.FontManager.getSingleton().destroyAll()
        PyCEGUI.ImageManager.getSingleton().destroyAll()
        PyCEGUI.SchemeManager.getSingleton().destroyAll()
        PyCEGUI.WidgetLookManager.getSingleton().eraseAllWidgetLooks()
        
        progress.setLabelText("Setting resource paths...")
        progress.setValue(1)
        
        self.setResourceGroupDirectory("imagesets", project.getAbsolutePathOf(project.imagesetsPath))
        self.setResourceGroupDirectory("fonts", project.getAbsolutePathOf(project.fontsPath))
        self.setResourceGroupDirectory("schemes", project.getAbsolutePathOf(project.schemesPath))
        self.setResourceGroupDirectory("looknfeels", project.getAbsolutePathOf(project.looknfeelsPath))
        self.setResourceGroupDirectory("layouts", project.getAbsolutePathOf(project.layoutsPath))
        
        progress.setLabelText("Recreating all schemes...")
        progress.setValue(2)
        
        for scheme in schemes:
            progress.setValue(progress.value() + 1)
            progress.setLabelText("Recreating all schemes... (%s)" % (scheme))
            PyCEGUI.SchemeManager.getSingleton().createFromFile(scheme, "schemes")
            
        progress.reset()
        
    def getAvailableSkins(self):
        skins = []

        i = PyCEGUI.WindowFactoryManager.getSingleton().getFalagardMappingIterator()

        while not i.isAtEnd():
            current_skin = i.getCurrentValue().d_windowType.split('/')[0]
            if current_skin not in skins:
                skins.append(current_skin)

            i.next()

        skins.sort()

        return skins
    
    def getAvailableFonts(self):
        fonts = []
        font_iter = PyCEGUI.FontManager.getSingleton().getIterator()
        while not font_iter.isAtEnd():
            fonts.append(font_iter.getCurrentValue().getName())
            font_iter.next()

        fonts.sort()

        return fonts
    
    def getAvailableWidgetsBySkin(self):
        ret = {}
        ret["__no_skin__"] = ["DefaultWindow", "DragDropContainer",
                             "VerticalLayoutContainer", "HorizontalLayoutContainer",
                             "GridLayoutContainer"]

        i = PyCEGUI.WindowFactoryManager.getSingleton().getFalagardMappingIterator()
        while not i.isAtEnd():
            #base = i.getCurrentValue().d_baseType
            mapped_type = i.getCurrentValue().d_windowType.split('/')
            look = mapped_type[0]
            widget = mapped_type[1]

            # insert empty list for the look if it's a new look
            if not look in ret:
                ret[look] = []

            # append widget name to the list for it's look
            ret[look].append(widget)

            i.next()

        # sort the lists
        for look in ret:
            ret[look].sort()

        return ret
    
    def makeGLContextCurrent(self):
        self.view.viewport().makeCurrent()
        
    def activate(self, parentWidget, resourceIdentifier, scene = None):
        """Activates the CEGUI Widget for the given parentWidget (QWidget derived class).
        resourceIdentifier is usually absolute path of the file and is used to differentiate
        resolution settings
        """
        
        # sometimes things get called in the opposite order, lets be forgiving and robust!
        if self.currentParentWidget is not None:
            self.deactivate(self.currentParentWidget)
            
        self.currentParentWidget = parentWidget
        
        if scene is None:
            scene = GraphicsScene()
        
        self.currentParentWidget.setUpdatesEnabled(False)
        self.view.setScene(scene)
        if self.currentParentWidget.layout():
            self.currentParentWidget.layout().addWidget(self)
        else:
            self.setParent(self.currentParentWidget)
        self.currentParentWidget.setUpdatesEnabled(True)
        
        # cause full redraw to ensure nothing gets stuck
        PyCEGUI.System.getSingleton().signalRedraw()
        
        # and mark the view as dirty
        self.view.update()
        
    def deactivate(self, parentWidget):
        if self.currentParentWidget != parentWidget:
            return
            
        self.currentParentWidget.setUpdatesEnabled(False)
        self.view.setScene(None)
        if self.currentParentWidget.layout():
            self.currentParentWidget.layout().removeWidget(self)
        else:
            self.setParentWidget(None)
        self.currentParentWidget.setUpdatesEnabled(True)
            
        self.currentParentWidget = None
        
    def getWidgetPreviewImage(self, widgetType, previewWidth = 128, previewHeight = 64):
        self.ensureCEGUIIsInitialised()
        
        self.makeGLContextCurrent()

        system = PyCEGUI.System.getSingleton()
        #system.signalRedraw()

        renderer = system.getRenderer()
        
        renderTarget = PyCEGUIOpenGLRenderer.OpenGLViewportTarget(renderer)
        renderTarget.setArea(PyCEGUI.Rectf(0, 0, previewWidth, previewHeight))
        renderingSurface = PyCEGUI.RenderingSurface(renderTarget)
        
        widgetInstance = PyCEGUI.WindowManager.getSingleton().createWindow(widgetType, "preview")
        widgetInstance.setRenderingSurface(renderingSurface)
        # set it's size and position so that it shows up
        widgetInstance.setPosition(PyCEGUI.UVector2(PyCEGUI.UDim(0, 0), PyCEGUI.UDim(0, 0)))
        widgetInstance.setSize(PyCEGUI.USize(PyCEGUI.UDim(0, previewWidth), PyCEGUI.UDim(0, previewHeight)))
        # fake update to ensure everything is set
        widgetInstance.update(1)
        
        temporaryFBO = QGLFramebufferObject(previewWidth, previewHeight, GL_TEXTURE_2D)
        temporaryFBO.bind()
        
        renderingSurface.invalidate()

        renderer.beginRendering()
        
        try:
            widgetInstance.render()
        
        finally:
            # no matter what happens we have to clean after ourselves!
            
            renderer.endRendering()
            temporaryFBO.release()
            PyCEGUI.WindowManager.getSingleton().destroyWindow(widgetInstance)
        
        return temporaryFBO.toImage()
        
    def slot_autoExpandChanged(self, expand):
        if expand == Qt.Checked:
            #self.view.setWidgetResizable(True)
            #self.view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            pass
        else:
            pass
        
            #self.biew.setWidgetResizable(False)
            #self.view.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
            
            # set the currently preferred size
            #self.slot_resolutionBoxChanged(self.resolutionBox.currentText())
                
    def slot_resolutionBoxChanged(self, text):
        if text == "Project Default (Layout)":
            # special case
            pass
        else:
            res = text.split("x", 1)
            if len(res) == 2:
                try:
                    width = int(res[0])
                    height = int(res[1])
                    
                    if width < 1:
                        width = 1
                    if height < 1:
                        height = 1
                    
                    self.makeGLContextCurrent()
                    self.view.scene().setCEGUIDisplaySize(width, height, lazyUpdate = False)
                    
                except AttributeError:
                    # ignore invalid literals
                    pass

    def slot_debugInfoButton(self):
        self.debugInfo.show()

# make it visible to the outside
import widgethelpers
