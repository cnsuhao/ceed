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
import ceed.ui.bitmapeditor

##
# A simple external bitmap editor starter/image viewer
class BitmapTabbedEditor(editors.TabbedEditor, QWidget):
    def __init__(self, filePath):
        # TODO: maybe I am doing this wrong since I am not using super,
        #       I need to pass 2 different argument sets so I am doing it explicit
        #super(BitmapTabbedEditor, self).__init__(filePath)
        
        editors.TabbedEditor.__init__(self, None, filePath)
        QWidget.__init__(self)
        
        self.ui = ceed.ui.bitmapeditor.Ui_BitmapEditor()
        self.ui.setupUi(self)
        
        self.tabWidget = self
    
    def initialise(self, mainWindow):
        super(BitmapTabbedEditor, self).initialise(mainWindow)
            
        self.preview = self.findChild(QLabel, "preview")
        self.preview.setPixmap(QPixmap(self.filePath))
    
    def finalise(self):
        super(BitmapTabbedEditor, self).finalise()
        
        self.tabWidget = None
        
    def hasChanges(self):
        return False

class BitmapTabbedEditorFactory(editors.TabbedEditorFactory):
    def getFileExtensions(self):
        extensions = ["png", "jpg", "jpeg", "tga", "dds"]
        return extensions

    def canEditFile(self, filePath):
        extensions = self.getFileExtensions()
        
        for extension in extensions:
            if filePath.endswith("." + extension):
                return True
            
        return False

    def create(self, filePath):
        return BitmapTabbedEditor(filePath)
