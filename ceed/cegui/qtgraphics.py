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

import math
import PyCEGUI

from ceed import resizable
from ceed import cegui

class GraphicsScene(QGraphicsScene):
    """A scene that draws CEGUI as it's background.
    
    Subclass this to be able to show Qt graphics items and widgets
    on top of the embedded CEGUI widget!
    
    Interaction is also supported
    """
    
    def __init__(self, ceguiInstance):
        super(GraphicsScene, self).__init__()
        
        self.ceguiInstance = ceguiInstance
        self.scenePadding = 100
        # reasonable defaults I think
        self.setCEGUIDisplaySize(800, 600, lazyUpdate = True)
        
        self.fbo = None
        
    def setCEGUIDisplaySize(self, width, height, lazyUpdate = True):
        self.ceguiDisplaySize = PyCEGUI.Sizef(width, height)
        self.setSceneRect(QRectF(-self.scenePadding, -self.scenePadding,
                                 width + 2 * self.scenePadding, height + 2 * self.scenePadding))
        
        if not lazyUpdate:
            # FIXME: Change when multi root is in CEGUI core
            PyCEGUI.System.getSingleton().notifyDisplaySizeChanged(self.ceguiDisplaySize)
            
        self.fbo = None

    def drawBackground(self, painter, rect):
        """We override this and draw CEGUI instead of the whole background.    
        This method uses a FBO to implement zooming, scrolling around, etc...
        
        FBOs are therefore required by CEED and it won't run without a GPU that supports them.
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
                
        self.ceguiInstance.ensureIsInitialised()
        
        if self.ceguiDisplaySize != PyCEGUI.System.getSingleton().getRenderer().getDisplaySize():
            # FIXME: Change when multi root is in CEGUI core
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
        if bool(glActiveTexture):
            glActiveTexture(GL_TEXTURE0)
        
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.fbo.texture())

        # TODO: I was told that this is the slowest method to draw with OpenGL, with which I certainly agree
        #       no profiling has been done at all and I don't suspect this to be a painful performance problem.
        #       However changing this to a less pathetic rendering method would be great.

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

class GraphicsView(resizable.GraphicsView, cegui.GLContextProvider):
    """This is a final class, not suitable for subclassing. This views given scene
    using QGLWidget. It's designed to work with cegui.GraphicsScene derived classes.
    """
    
    def __init__(self, parent = None):
        resizable.GraphicsView.__init__(self, parent)

        self.setViewport(QGLWidget())
        # OpenGL doesn't do partial redraws (it isn't practical anyways)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        
        self.injectInput = False
        # we might want mouse events
        self.setMouseTracking(True)
        # we might want key events
        self.setFocusPolicy(Qt.ClickFocus)
        
        # if True, we render always (possibly capped to some FPS) - suitable for live preview
        # if False, we render only when update() is called - suitable for visual editing
        self.continuousRendering = True
        # only applies when we are rendering continuously, it's the max FPS that we will try to achieve
        self.continuousRenderingTargetFPS = 60

    def makeGLContextCurrent(self):
        self.viewport().makeCurrent()

    def drawBackground(self, painter, rect):
        super(GraphicsView, self).drawBackground(painter, rect)
        
        if self.continuousRendering:
            if self.continuousRenderingTargetFPS <= 0:
                self.updateSelfAndScene()
                
            else:
                # FIXME: this is actually wrong, we have to measure how long it takes us to render and count that in!
                # * 1000 because QTimer thinks in milliseconds
                QTimer.singleShot(1.0 / self.continuousRenderingTargetFPS * 1000, self.updateSelfAndScene)
        
        else:
            # we don't mark ourselves as dirty if user didn't request continuous rendering
            pass
    
    def updateSelfAndScene(self):
        self.update()
        
        scene = self.scene()
        if scene:
            scene.update()
        
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
