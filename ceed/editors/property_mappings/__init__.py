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

from PySide.QtGui import *

from ceed import editors
from ceed import propertyinspector
import ceed.compatibility.property_mappings as property_mappings_compatibility

from xml.etree import ElementTree

##
# Property mapping file editor
class PropertyMappingsTabbedEditor(editors.UndoStackTabbedEditor):
    def __init__(self, filePath):
        
        super(PropertyMappingsTabbedEditor, self).__init__(property_mappings_compatibility.Manager.instance, filePath)
        
        self.tabWidget = QTableView()
        self.tabWidget.setDragDropMode(QAbstractItemView.InternalMove)
        self.tabWidget.setDragDropOverwriteMode(False)
        self.tabWidget.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        #self.tabWidget.setRootIsDecorated(False)
        
        self.propertyMappingList = None
    
    def initialise(self, mainWindow):
        super(PropertyMappingsTabbedEditor, self).initialise(mainWindow)
        
        if self.nativeData != "":
            self.propertyMappingList = propertyinspector.PropertyInspectorMappingList()
            self.propertyMappingList.loadFromElement(ElementTree.fromstring(self.nativeData))
            
            self.tabWidget.setModel(self.propertyMappingList)
            
    def finalise(self):
        super(PropertyMappingsTabbedEditor, self).finalise()
        
        self.tabWidget = None

class PropertyMappingsTabbedEditorFactory(editors.TabbedEditorFactory):
    def getFileExtensions(self):
        extensions = {"pmappings"}
        return extensions

    def canEditFile(self, filePath):
        extensions = self.getFileExtensions()
        
        for extension in extensions:
            if filePath.endswith("." + extension):
                return True
            
        return False

    def create(self, filePath):
        return PropertyMappingsTabbedEditor(filePath)
