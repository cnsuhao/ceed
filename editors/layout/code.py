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

import editors.mixed
import PyCEGUI

class CodeEditing(editors.mixed.CodeEditMode):
    def __init__(self, tabbedEditor):
        super(CodeEditing, self).__init__()
        
        self.tabbedEditor = tabbedEditor
        
    def getNativeCode(self):
        if not self.tabbedEditor.visual.rootWidget:
            return ""
        
        return PyCEGUI.WindowManager.getSingleton().getLayoutAsString(self.tabbedEditor.visual.rootWidget)
        
    def propagateNativeCode(self, code):
        # we have to make the context the current context to ensure textures are fine
        mainwindow.MainWindow.instance.ceguiContainerWidget.makeGLContextCurrent()
        
        try:
            newRoot = PyCEGUI.WindowManager.getSingleton().loadLayoutFromString(code)
            self.tabbedEditor.visual.replaceRootWidget(newRoot)
            
            return True
        
        except:
            return False
        
# needs to be at the end, imported to get the singleton
import mainwindow
