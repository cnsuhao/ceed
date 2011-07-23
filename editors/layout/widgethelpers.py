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
    """See cegui.widgethelpers.SerialisationData
    
    The only reason for this class is that we need to create the correct Manipulator (not it's base class!)
    """
    
    def __init__(self, visual, widget = None, serialiseChildren = True):
        self.visual = visual
        
        super(SerialisationData, self).__init__(widget, serialiseChildren)
        
    def createChildData(self, widget = None, serialiseChildren = True):
        return SerialisationData(self.visual, widget, serialiseChildren)
        
    def createManipulator(self, parentManipulator, widget, recursive = True, skipAutoWidgets = True):
        return Manipulator(self.visual, parentManipulator, widget, recursive, skipAutoWidgets)
    
    def setVisual(self, visual):
        self.visual = visual
        
        for child in self.children:
            child.setVisual(visual)
       
    def reconstruct(self, rootManipulator):
        ret = super(SerialisationData, self).reconstruct(rootManipulator)
        
        if ret.widget.getParent() is None:
            # this is a root widget being reconstructed, handle this accordingly
            self.visual.setRootWidgetManipulator(ret)
        
        return ret
            
class Manipulator(cegui.widgethelpers.Manipulator):
    """Layout editing specific widget manipulator"""
    snapGridBrush = None
    
    @classmethod
    def getSnapGridBrush(cls):
        if cls.snapGridBrush is None:
            cls.snapGridBrush = QBrush()
            texture = QPixmap(settings.getEntry("layout/visual/snap_grid_x").value, settings.getEntry("layout/visual/snap_grid_y").value)
            texture.fill(QColor(Qt.transparent))
            
            painter = QPainter(texture)
            painter.setPen(QPen(settings.getEntry("layout/visual/snap_grid_point_colour").value))
            painter.drawPoint(0, 0)
            painter.setPen(QPen(settings.getEntry("layout/visual/snap_grid_point_shadow_colour").value))
            painter.drawPoint(1, 0)
            painter.drawPoint(1, 1)
            painter.drawPoint(0, 1)
            painter.end()
            
            cls.snapGridBrush.setTexture(texture)
            
        return cls.snapGridBrush
    
    def __init__(self, visual, parent, widget, recursive = True, skipAutoWidgets = True):
        self.visual = visual
        
        super(Manipulator, self).__init__(parent, widget, recursive, skipAutoWidgets)  
        
        self.setAcceptDrops(True)
        self.drawSnapGrid = False
        self.ignoreSnapGrid = False
        self.snapGridAction = action.getAction("layout/snap_grid")
    
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
    
    def detach(self, destroyWidget):
        parentWidgetWasNone = self.widget.getParent() is None
        super(Manipulator, self).detach(destroyWidget)

        if parentWidgetWasNone:
            # if this was root we have to inform the scene accordingly!
            self.visual.setRootWidgetManipulator(None)

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-ceed-widget-type"):
            event.acceptProposedAction()
            
            self.setPen(self.getDragAcceptableHintPen())
            
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        self.setPen(self.getNormalPen())

    def dropEvent(self, event):
        """Takes care of creating new widgets when user drops the right mime type here
        (dragging from the CreateWidgetDockWidget)
        """
        
        data = event.mimeData().data("application/x-ceed-widget-type")

        if data:
            widgetType = data.data()

            cmd = undo.CreateCommand(self.visual, self.widget.getNamePath(), widgetType, self.getUniqueChildWidgetName(widgetType.rsplit("/", 1)[-1]))
            self.visual.tabbedEditor.undoStack.push(cmd)

            event.acceptProposedAction()
            
        else:
            event.ignore()
    
    def notifyResizeStarted(self):
        super(Manipulator, self).notifyResizeStarted()
        
        parent = self.parentItem()
        if isinstance(parent, Manipulator):
            parent.drawSnapGrid = True
            
    def notifyResizeFinished(self, newPos, newRect):
        super(Manipulator, self).notifyResizeFinished(newPos, newRect)
        
        parent = self.parentItem()
        if isinstance(parent, Manipulator):
            parent.drawSnapGrid = False
            
    def notifyMoveStarted(self):
        super(Manipulator, self).notifyMoveStarted()
        
        parent = self.parentItem()
        if isinstance(parent, Manipulator):
            parent.drawSnapGrid = True
            
    def notifyMoveFinished(self, newPos):
        super(Manipulator, self).notifyMoveFinished(newPos)
        
        parent = self.parentItem()
        if isinstance(parent, Manipulator):
            parent.drawSnapGrid = False
    
    def paint(self, painter, option, widget):
        super(Manipulator, self).paint(painter, option, widget)
        
        if self.drawSnapGrid and self.snapGridAction.isChecked():
            painter.save()
            painter.fillRect(self.boundingRect(), Manipulator.getSnapGridBrush())
            painter.restore()
    
    def updateFromWidget(self):
        # we are updating the position and size from widget, we don't want any snapping
        self.ignoreSnapGrid = True
        super(Manipulator, self).updateFromWidget()
        self.ignoreSnapGrid = False
    
    def snapXCoordToGrid(self, x):
        # point is in local space
        snapGridX = settings.getEntry("layout/visual/snap_grid_x").value
        return round(x / snapGridX) * snapGridX
    
    def snapYCoordToGrid(self, y):
        # point is in local space
        snapGridY = settings.getEntry("layout/visual/snap_grid_y").value
        return round(y / snapGridY) * snapGridY
    
    def constrainMovePoint(self, point):
        if not self.ignoreSnapGrid and hasattr(self, "snapGridAction") and self.snapGridAction.isChecked():
            parent = self.parentItem()
            if isinstance(parent, Manipulator):
                point = QPointF(self.snapXCoordToGrid(point.x()), self.snapYCoordToGrid(point.y()))
        
        point = super(Manipulator, self).constrainMovePoint(point)
        
        return point
    
    def constrainResizeRect(self, rect, oldRect):
        # we constrain all 4 "corners" to the snap grid if needed
        if not self.ignoreSnapGrid and hasattr(self, "snapGridAction") and self.snapGridAction.isChecked():
            parent = self.parentItem()
            if isinstance(parent, Manipulator):
                # we only snap the coordinates that have changed
                # because for example when you drag the left edge you don't want the right edge to snap!
                
                # we have to add the position coordinate as well to ensure the snap is precisely at the guide point
                # it is subtracted later on because the rect is relative to the item position
                
                if rect.left() != oldRect.left():
                    rect.setLeft(self.snapXCoordToGrid(self.pos().x() + rect.left()) - self.pos().x())
                if rect.top() != oldRect.top():
                    rect.setTop(self.snapYCoordToGrid(self.pos().y() + rect.top()) - self.pos().y())
                    
                if rect.right() != oldRect.right():
                    rect.setRight(self.snapXCoordToGrid(self.pos().x() + rect.right()) - self.pos().x())
                if rect.bottom() != oldRect.bottom():
                    rect.setBottom(self.snapYCoordToGrid(self.pos().y() + rect.bottom()) - self.pos().y())
                
        rect = super(Manipulator, self).constrainResizeRect(rect, oldRect)
        
        return rect
        
import settings
import action
