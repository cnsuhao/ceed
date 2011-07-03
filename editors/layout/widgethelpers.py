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

import cegui.widgethelpers
import undo

class SerialisationData(cegui.widgethelpers.SerialisationData):
    def __init__(self, visual, widget = None, serialiseChildren = True):
        self.visual = visual
        
        super(SerialisationData, self).__init__(widget, serialiseChildren)
        
    def createChildData(self, widget = None, serialiseChildren = True):
        return SerialisationData(self.visual, widget, serialiseChildren)
        
    def createManipulator(self, parentManipulator, widget, recursive = True, skipAutoWidgets = True):
        return Manipulator(self.visual, parentManipulator, widget, recursive, skipAutoWidgets)
        
class Manipulator(cegui.widgethelpers.Manipulator):
    def __init__(self, visual, parent, widget, recursive = True, skipAutoWidgets = True):
        self.visual = visual
        
        super(Manipulator, self).__init__(parent, widget, recursive, skipAutoWidgets)  
        
        self.setAcceptDrops(True)      
    
    def getNormalPen(self):
        return settings.getEntry("layout/visual/normal_outline").value
        
    def getHoverPen(self):
        return settings.getEntry("layout/visual/hover_outline").value
    
    def getPenWhileResizing(self):
        return settings.getEntry("layout/visual/resizing_outline").value
    
    def getPenWhileMoving(self):
        return settings.getEntry("layout/visual/moving_outline").value
    
    """
    def getEdgeResizingHandleHoverPen(self):
        ret = QPen()
        ret.setColor(QColor(0, 255, 255, 255))
        ret.setWidth(2)
        ret.setCosmetic(True)
        
        return ret
    
    def getEdgeResizingHandleHiddenPen(self):
        ret = QPen()
        ret.setColor(Qt.transparent)
        
        return ret
    
    def getCornerResizingHandleHoverPen(self):
        ret = QPen()
        ret.setColor(QColor(0, 255, 255, 255))
        ret.setWidth(2)
        ret.setCosmetic(True)
        
        return ret    
    
    def getCornerResizingHandleHiddenPen(self):
        ret = QPen()
        ret.setColor(Qt.transparent)
        
        return ret
    """
    def getDragAcceptableHintPen(self):
        ret = QPen()
        ret.setColor(QColor(255, 255, 0))
        
        return ret
        
    def getUniqueChildWidgetName(self, base = "Widget"):
        candidate = base
        
        if self.widget is None:
            return candidate
        
        i = 2
        while self.widget.isChild(candidate):
            candidate = "%s%i" % (base, i)
            i += 1
            
        return candidate
        
    def createChildManipulator(self, childWidget, recursive = True, skipAutoWidgets = True):
        return Manipulator(self.visual, self, childWidget, recursive, skipAutoWidgets)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-cegui-widget-type"):
            event.acceptProposedAction()
            
            self.setPen(self.getDragAcceptableHintPen())
            
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.setPen(self.getNormalPen())

    def dropEvent(self, event):
        data = event.mimeData().data("application/x-cegui-widget-type")

        if data:
            widgetType = data.data()

            cmd = undo.CreateCommand(self.visual, self.widget.getNamePath(), widgetType, self.getUniqueChildWidgetName(widgetType.rsplit("/", 1)[-1]))
            self.visual.tabbedEditor.undoStack.push(cmd)

            event.acceptProposedAction()
            
        else:
            event.ignore()
            
import settings
