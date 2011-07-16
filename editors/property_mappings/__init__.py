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
import editors

##
# Property mapping file editor
class PropertyMappingsEditor(editors.UndoStackTabbedEditor):
    def __init__(self, filePath):
        
        super(PropertyMappingsEditor, self).__init__(None, filePath)
        
        self.tabWidget = QTableView()
    
    def initialise(self, mainWindow):
        super(PropertyMappingsEditor, self).initialise(mainWindow)
            
    def finalise(self):
        super(PropertyMappingsEditor, self).finalise()
        
        self.tabWidget = None

class PropertyMappingsEditorFactory(editors.TabbedEditorFactory):
    def canEditFile(self, filePath):
        extensions = ["pmappings"]
        
        for extension in extensions:
            if filePath.endswith("." + extension):
                return True
            
        return False

    def create(self, filePath):
        return PropertyMappingsEditor(filePath)
