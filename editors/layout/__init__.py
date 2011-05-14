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

import editors
import xmledit

import visual
import xmlediting
import preview

import PyCEGUI

from xml.etree import ElementTree

class LayoutTabbedEditor(editors.mixed.MixedTabbedEditor):
    """Binds all layout editing functionality together
    """
    
    def __init__(self, filePath):
        super(LayoutTabbedEditor, self).__init__(filePath)
        
        self.requiresProject = True
        
        self.visual = visual.VisualEditing(self)
        self.addTab(self.visual, "Visual")
        
        self.xml = xmlediting.XMLEditing(self)
        self.addTab(self.xml, "XML")
        
        self.previewer = preview.LayoutPreviewer(self)
        self.addTab(self.previewer, "Live Preview")
        
        self.tabWidget = self
    
    def initialise(self, mainWindow):
        super(LayoutTabbedEditor, self).initialise(mainWindow)
        
        # we have to make the context the current context to ensure textures are fine
        self.mainWindow.ceguiContainerWidget.makeGLContextCurrent()
        # TODO: Not the proper path handling for now!!
        root = PyCEGUI.WindowManager.getSingleton().loadLayoutFromFile(os.path.basename(self.filePath), "")
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
        
    def deactivate(self):
        self.mainWindow.removeDockWidget(self.visual.hierarchyDockWidget)
        self.mainWindow.removeDockWidget(self.visual.propertiesDockWidget)
        self.mainWindow.removeDockWidget(self.visual.createWidgetDockWidget)
        
        super(LayoutTabbedEditor, self).deactivate()
        
    def saveAs(self, targetPath, updateCurrentPath = True):
        xmlmode = self.currentWidget() == self.xml
        
        # if user saved in xml mode, we process the xml by propagating it to visual
        # (allowing the change propagation to do the xml validating and other work for us)
        
        if xmlmode:
            self.xml.propagateChangesToVisual()
            
        source = PyCEGUI.WindowManager.getSingleton().getLayoutAsString(self.visual.rootWidget)
        
        f = open(targetPath, "w")
        f.write(source)
        f.close()
        
        super(LayoutTabbedEditor, self).saveAs(targetPath, updateCurrentPath)

class LayoutTabbedEditorFactory(editors.TabbedEditorFactory):
    def canEditFile(self, filePath):
        extensions = [".layout"]
        
        for extension in extensions:
            if filePath.endswith(extension):
                return True
            
        return False

    def create(self, filePath):
        return LayoutTabbedEditor(filePath)
