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
import compatibility.animation_list

from xml.etree import ElementTree

import visual
import code

##
# Animation list file editor (XML file containing list of animations)
class AnimationListEditor(editors.mixed.MixedTabbedEditor):
    def __init__(self, filePath):
        
        super(AnimationListEditor, self).__init__(compatibility.animation_list.Manager.instance, filePath)
        
        self.visual = visual.VisualEditing(self)
        self.addTab(self.visual, "Visual")
        
        self.code = code.CodeEditing(self)
        self.addTab(self.code, "Code")
        
        self.tabWidget = self
    
    def initialise(self, mainWindow):
        super(AnimationListEditor, self).initialise(mainWindow)
        
        if self.nativeData != "":
            pass
            
    def finalise(self):
        super(AnimationListEditor, self).finalise()
        
        self.tabWidget = None

class AnimationListEditorFactory(editors.TabbedEditorFactory):
    def canEditFile(self, filePath):
        extensions = ["anims"]
        
        for extension in extensions:
            if filePath.endswith("." + extension):
                return True
            
        return False

    def create(self, filePath):
        return AnimationListEditor(filePath)
