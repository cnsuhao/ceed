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

import tab
import mixedtab
import xmledit

import undo

import visual
import xmlediting

from xml.etree import ElementTree

class ImagesetTabbedEditor(mixedtab.MixedTabbedEditor):
    """Binds all imageset editing functionality together
    """
    
    def __init__(self, filePath):
        super(ImagesetTabbedEditor, self).__init__(filePath)
        
        self.visual = visual.VisualEditing(self)
        self.addTab(self.visual, "Visual")
        
        self.xml = xmlediting.XMLEditing(self)
        self.addTab(self.xml, "XML")
        
        self.tabWidget = self
    
    def initialise(self, mainWindow):
        super(ImagesetTabbedEditor, self).initialise(mainWindow)
    
        root = None
        try:
            tree = ElementTree.parse(self.filePath)
            root = tree.getroot()
            
        except:
            # things didn't go smooth
            # 2 reasons for that
            #  * the file is empty
            #  * the contents of the file are invalid
            #
            # In the first case we will silently move along (it is probably just a new file),
            # in the latter we will output a message box informing about the situation
            
            # the file should exist at this point, so we are not checking and letting exceptions
            # fly out of this method
            if os.path.getsize(self.filePath) > 2:
                # the file contains more than just CR LF
                QMessageBox.question(self,
                                     "Can't parse given imageset!",
                                     "Parsing '%s' failed, it's most likely not a valid XML file. "
                                     "Constructing empty imageset instead (if you save you will override the invalid data!). "
                                     "Exception details follow: %s" % (self.filePath, sys.exc_info()[0]),
                                     QMessageBox.Ok)
            
            # we construct the minimal empty imageset    
            root = ElementTree.Element("Imageset")
            root.set("Name", "")
            root.set("Imagefile", "")
        
        self.visual.initialise(root)
    
    def finalise(self):        
        super(ImagesetTabbedEditor, self).finalise()
        
        self.tabWidget = None
    
    def activate(self):
        super(ImagesetTabbedEditor, self).activate()
        
        self.mainWindow.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.visual.toolBar)
        self.visual.toolBar.show()
        
        self.mainWindow.addDockWidget(Qt.LeftDockWidgetArea, self.visual.dockWidget)
        self.visual.dockWidget.setVisible(True)
        
    def deactivate(self):
        self.mainWindow.removeDockWidget(self.visual.dockWidget)
        self.mainWindow.removeToolBar(self.visual.toolBar)
        
        super(ImagesetTabbedEditor, self).deactivate()
        
    def saveAs(self, targetPath):
        xmlmode = self.currentWidget() == self.xml
        
        # if user saved in xml mode, we process the xml by propagating it to visual
        # (allowing the change propagation to do the xml validating and other work for us)
        
        if xmlmode:
            self.xml.propagateChangesToVisual()
            
        rootElement = self.visual.imagesetEntry.saveToElement()
        # we indent to make the resulting files as readable as possible
        xmledit.indent(rootElement)
        
        tree = ElementTree.ElementTree(rootElement)
        tree.write(targetPath, "utf-8")
        
        super(ImagesetTabbedEditor, self).saveAs(targetPath)

class ImagesetTabbedEditorFactory(tab.TabbedEditorFactory):
    def canEditFile(self, filePath):
        extensions = [".imageset"]
        
        for extension in extensions:
            if filePath.endswith(extension):
                return True
            
        return False

    def create(self, filePath):
        return ImagesetTabbedEditor(filePath)
