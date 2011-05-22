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
import PyCEGUI
import qtgraphics

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

# we import here to avoid circular dependencies (GraphicsView has to be defined at this point)
import ui.ceguicontainerwidget

class ContainerWidget(QWidget):
    """
    This widget is what you should use (alongside your GraphicsScene derived class) to
    put CEGUI inside parts of the editor.
    
    Provides resolution changes, auto expanding and debug widget
    """
    
    def __init__(self, ceguiInstance):
        super(ContainerWidget, self).__init__()
        
        self.ceguiInstance = ceguiInstance
        
        self.ui = ui.ceguicontainerwidget.Ui_CEGUIContainerWidget()
        self.ui.setupUi(self)
        
        self.currentParentWidget = None

        self.debugInfo = DebugInfo(self)
        self.view = self.findChild(qtgraphics.GraphicsView, "view")
        self.ceguiInstance.setGLContextProvider(self.view)
        self.view.setBackgroundRole(QPalette.Dark)
        self.view.containerWidget = self
        
        self.autoExpand = self.findChild(QCheckBox, "autoExpand")
        self.autoExpand.stateChanged.connect(self.slot_autoExpandChanged)
        self.resolutionBox = self.findChild(QComboBox, "resolutionBox")
        self.resolutionBox.editTextChanged.connect(self.slot_resolutionBoxChanged)
        
        self.debugInfoButton = self.findChild(QPushButton, "debugInfoButton")
        self.debugInfoButton.clicked.connect(self.slot_debugInfoButton)
    
    def enableInput(self):
        self.view.injectInput = True
        
    def disableInput(self):
        self.view.injectInput = False        
    
    def makeGLContextCurrent(self):
        self.view.viewport().makeCurrent()
    
    def setViewFeatures(self, wheelZoom, middleButtonScroll):
        # always zoom to the original 100% when changing view features
        self.view.zoomOriginal()
        self.view.wheelZoomEnabled = wheelZoom
        
        self.view.middleButtonDragScrollEnabled = middleButtonScroll
        
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
            scene = qtgraphics.GraphicsScene(self.ceguiInstance)
        
        self.currentParentWidget.setUpdatesEnabled(False)
        self.view.setScene(scene)
        # make sure the resolution is set right for the given scene
        self.slot_resolutionBoxChanged(self.resolutionBox.currentText())
        
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
        # back to the defaults
        self.setViewFeatures(False, False)
        self.view.setScene(None)
        
        if self.currentParentWidget.layout():
            self.currentParentWidget.layout().removeWidget(self)
        else:
            self.setParentWidget(None)
        self.currentParentWidget.setUpdatesEnabled(True)
            
        self.currentParentWidget = None
        
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
                    
                    self.ceguiInstance.makeGLContextCurrent()
                    self.view.scene().setCEGUIDisplaySize(width, height, lazyUpdate = False)
                    
                except AttributeError:
                    # ignore invalid literals
                    pass

    def slot_debugInfoButton(self):
        self.debugInfo.show()
