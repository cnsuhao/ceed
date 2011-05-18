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
from PySide.QtCore import *

import editors.mixed

import PyCEGUI

class LayoutPreviewer(QWidget, editors.mixed.EditMode):
    def __init__(self, tabbedEditor):
        super(LayoutPreviewer, self).__init__()
        
        self.tabbedEditor = tabbedEditor
        self.rootWidget = None
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

    def activate(self):
        super(LayoutPreviewer, self).activate()

        assert(self.rootWidget is None)
        
        # we have to make the context the current context to ensure textures are fine
        mainwindow.MainWindow.instance.ceguiContainerWidget.makeGLContextCurrent()
        
        # lets clone so we don't affect the layout at all
        self.rootWidget = self.tabbedEditor.visual.rootWidget.clone()
        PyCEGUI.System.getSingleton().setGUISheet(self.rootWidget)
        
    def deactivate(self):    
        PyCEGUI.WindowManager.getSingleton().destroyWindow(self.rootWidget)
        self.rootWidget = None

        return super(LayoutPreviewer, self).deactivate()

    def showEvent(self, event):
        super(LayoutPreviewer, self).showEvent(event)

        mainwindow.MainWindow.instance.ceguiContainerWidget.activate(self, self.tabbedEditor.filePath)
        mainwindow.MainWindow.instance.ceguiContainerWidget.enableInput()
        
        if self.rootWidget:
            PyCEGUI.System.getSingleton().setGUISheet(self.rootWidget)

    def hideEvent(self, event):
        mainwindow.MainWindow.instance.ceguiContainerWidget.disableInput()
        mainwindow.MainWindow.instance.ceguiContainerWidget.deactivate(self)

        if self.rootWidget:
            PyCEGUI.System.getSingleton().setGUISheet(None)
            
        super(LayoutPreviewer, self).hideEvent(event)

# needs to be at the end, import to get the singleton
import mainwindow
