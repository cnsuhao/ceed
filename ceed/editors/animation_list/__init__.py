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

from ceed import editors
import ceed.compatibility.animation_list as animation_list_compatibility
from ceed.editors.animation_list import visual
from ceed.editors.animation_list import code

from xml.etree import ElementTree

class AnimationListTabbedEditor(editors.mixed.MixedTabbedEditor):
    """Animation list file editor (XML file containing list of animations)
    """
    
    def __init__(self, filePath):
        
        super(AnimationListTabbedEditor, self).__init__(animation_list_compatibility.Manager.instance, filePath)
        
        self.visual = visual.VisualEditing(self)
        self.addTab(self.visual, "Visual")
        
        self.code = code.CodeEditing(self)
        self.addTab(self.code, "Code")
        
        self.tabWidget = self
    
    def initialise(self, mainWindow):
        super(AnimationListTabbedEditor, self).initialise(mainWindow)
        
        if self.nativeData != "":
            pass
            
    def finalise(self):
        super(AnimationListTabbedEditor, self).finalise()
        
        self.tabWidget = None
        
    def activate(self):
        super(AnimationListTabbedEditor, self).activate()
        
        self.mainWindow.addDockWidget(Qt.LeftDockWidgetArea, self.visual.animationListDockWidget)
        self.visual.animationListDockWidget.setVisible(True)
        self.mainWindow.addDockWidget(Qt.BottomDockWidgetArea, self.visual.timelineDockWidget)
        self.visual.timelineDockWidget.setVisible(True)
        
    def deactivate(self):
        self.mainWindow.removeDockWidget(self.visual.animationListDockWidget)
        self.mainWindow.removeDockWidget(self.visual.timelineDockWidget)
        
        super(AnimationListTabbedEditor, self).deactivate()

class AnimationListTabbedEditorFactory(editors.TabbedEditorFactory):
    def canEditFile(self, filePath):
        extensions = ["anims"]
        
        for extension in extensions:
            if filePath.endswith("." + extension):
                return True
            
        return False

    def create(self, filePath):
        return AnimationListTabbedEditor(filePath)
