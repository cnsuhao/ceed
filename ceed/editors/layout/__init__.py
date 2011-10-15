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

import os
import sys

from ceed import editors
from ceed import xmledit

import ceed.compatibility.layout as layout_compatibility

import visual
import code
import preview

import PyCEGUI

from xml.etree import ElementTree

class LayoutTabbedEditor(editors.mixed.MixedTabbedEditor):
    """Binds all layout editing functionality together
    """
    
    def __init__(self, filePath):
        super(LayoutTabbedEditor, self).__init__(layout_compatibility.Manager.instance, filePath)
        
        self.requiresProject = True
        
        self.visual = visual.VisualEditing(self)
        self.addTab(self.visual, "Visual")
        
        self.code = code.CodeEditing(self)
        self.addTab(self.code, "Code")
        
        # Layout Previewer is not actually an edit mode, you can't edit the layout from it,
        # however for everything to work smoothly we do push edit mode changes to it to the
        # undo stack.
        #
        # TODO: This could be improved at least a little bit if 2 consecutive edit mode changes
        #       looked like this: A->Preview, Preview->C.  We could simply turn this into A->C,
        #       and if A = C it eat the undo command entirely.
        self.previewer = preview.LayoutPreviewer(self)
        self.addTab(self.previewer, "Live Preview")
        
        self.tabWidget = self
    
    def initialise(self, mainWindow):
        super(LayoutTabbedEditor, self).initialise(mainWindow)
        
        # we have to make the context the current context to ensure textures are fine
        self.mainWindow.ceguiContainerWidget.makeGLContextCurrent()
        
        root = None
        if self.nativeData != "":
            root = PyCEGUI.WindowManager.getSingleton().loadLayoutFromString(self.nativeData)
            
        self.visual.initialise(root)
    
    def finalise(self):        
        super(LayoutTabbedEditor, self).finalise()
        
        self.tabWidget = None
    
    def activate(self):
        super(LayoutTabbedEditor, self).activate()
        
        self.mainWindow.addDockWidget(Qt.LeftDockWidgetArea, self.visual.hierarchyDockWidget)
        self.visual.hierarchyDockWidget.setVisible(True)
        self.mainWindow.addDockWidget(Qt.RightDockWidgetArea, self.visual.propertiesDockWidget)
        self.visual.propertiesDockWidget.setVisible(True)
        self.mainWindow.addDockWidget(Qt.LeftDockWidgetArea, self.visual.createWidgetDockWidget)
        self.visual.createWidgetDockWidget.setVisible(True)
        self.mainWindow.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.visual.toolBar)
        self.visual.toolBar.show()
        
    def deactivate(self):
        self.mainWindow.removeDockWidget(self.visual.hierarchyDockWidget)
        self.mainWindow.removeDockWidget(self.visual.propertiesDockWidget)
        self.mainWindow.removeDockWidget(self.visual.createWidgetDockWidget)
        self.mainWindow.removeToolBar(self.visual.toolBar)
        
        super(LayoutTabbedEditor, self).deactivate()
        
    def saveAs(self, targetPath, updateCurrentPath = True):
        codeMode = self.currentWidget() is self.code
        
        # if user saved in code mode, we process the code by propagating it to visual
        # (allowing the change propagation to do the code validating and other work for us)
        
        if codeMode:
            self.code.propagateToVisual()
        
        currentRootWidget = self.visual.getCurrentRootWidget()
        
        if currentRootWidget is not None:    
            self.nativeData = PyCEGUI.WindowManager.getSingleton().getLayoutAsString(currentRootWidget)
        
        else:
            # empty layout
            self.nativeData = ""
        
        super(LayoutTabbedEditor, self).saveAs(targetPath, updateCurrentPath)

    def performCut(self):
        if self.currentWidget() is self.visual:
            return self.visual.performCut()
        
        return False

    def performCopy(self):
        if self.currentWidget() is self.visual:
            return self.visual.performCopy()
        
        return False
    
    def performPaste(self):
        if self.currentWidget() is self.visual:
            return self.visual.performPaste()
        
        return False

class LayoutTabbedEditorFactory(editors.TabbedEditorFactory):
    def canEditFile(self, filePath):
        extensions = layout_compatibility.Manager.instance.getAllPossibleExtensions()
        
        for extension in extensions:
            if filePath.endswith("." + extension):
                return True
            
        return False

    def create(self, filePath):
        return LayoutTabbedEditor(filePath)
