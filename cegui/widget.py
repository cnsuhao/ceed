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

import resizable
import PyCEGUI

# This module contains helping classes for CEGUI widget handling

class Manipulator(resizable.ResizableGraphicsRectItem):
    """
    This is a rectangle that is synchronised with given CEGUI widget,
    it provides moving and resizing functionality
    """
    
    def __init__(self, widget, recursive = True, skipAutoWidgets = True):
        """
        widget - CEGUI::Widget to wrap
        recursive - if true, even children of given widget are wrapped
        skipAutoWidgets - if true, auto widgets are skipped (only applicable if recursive is True)
        """
        
        super(Manipulator, self).__init__()
        
        self.setFlags(QGraphicsItem.ItemIsFocusable | 
                      QGraphicsItem.ItemIsSelectable |
                      QGraphicsItem.ItemIsMovable |
                      QGraphicsItem.ItemSendsGeometryChanges)

        self.widget = widget
        self.updateFromWidgetData()
        
        if recursive:
            idx = 0
            while idx < self.widget.getChildCount():
                childWidget = self.widget.getChildAtIdx(idx)
                
                if skipAutoWidgets and childWidget.isAutoWindow():
                    # TODO: non auto widgets inside auto widgets?
                    idx += 1
                    continue
                
                child = Manipulator(childWidget, True, skipAutoWidgets)
                child.setParentItem(self)
                
                idx += 1
                
    def updateFromWidgetData(self):
        assert(self.widget is not None)
        
        unclippedOuterRect = self.widget.getUnclippedOuterRect()
        pos = unclippedOuterRect.getPosition()
        size = unclippedOuterRect.getSize()
        
        parentWidget = self.widget.getParent()
        if parentWidget:
            parentUnclippedOuterRect = parentWidget.getUnclippedOuterRect()
            pos -= parentUnclippedOuterRect.getPosition()
        
        self.setPos(QPoint(pos.d_x, pos.d_y))
        self.setRect(QRectF(0, 0, size.d_width, size.d_height))
        
        for item in self.childItems():
            if not isinstance(item, Manipulator):
                continue
            
            item.updateFromWidgetData()
    
        self.preResizePosition = None
        self.preResizeSize = None
    
    def moveToFront(self):
        self.widget.moveToFront()
        
        parentItem = self.parentItem()
        if parentItem:
            for item in parentItem.childItems():
                if item == self:
                    continue
                
                # For some reason this is the opposite of what (IMO) it should be
                # which is self.stackBefore(item)
                #
                # Is Qt documentation flawed or something?!
                item.stackBefore(self)
                
            parentItem.moveToFront()
            
    def itemChange(self, change, value):    
        if change == QGraphicsItem.ItemSelectedHasChanged:
            if value:
                self.moveToFront()
        
        return super(Manipulator, self).itemChange(change, value)
    
    def notifyHandleSelected(self, handle):
        super(Manipulator, self).notifyHandleSelected(handle)
        
        self.moveToFront()
    
    def getMinSize(self):
        if self.widget:
            minPixelSize = PyCEGUI.CoordConverter.asAbsolute(self.widget.getMinSize(),
                                                             PyCEGUI.System.getSingleton().getRenderer().getDisplaySize())
            
            return QSizeF(minPixelSize.d_x, minPixelSize.d_y)
    
    def getMaxSize(self):
        if self.widget:
            maxPixelSize = PyCEGUI.CoordConverter.asAbsolute(self.widget.getMaxSize(),
                                                             PyCEGUI.System.getSingleton().getRenderer().getDisplaySize())
            
            return QSizeF(maxPixelSize.d_x, maxPixelSize.d_y)
    
    def notifyResizeStarted(self):
        super(Manipulator, self).notifyResizeStarted()
        
        self.preResizePosition = self.widget.getPosition()
        self.preResizeSize = self.widget.getSize()
        
        for item in self.childItems():
            if isinstance(item, Manipulator):
                item.setVisible(False)
    
    def notifyResizeProgress(self, newPos, newRect):
        super(Manipulator, self).notifyResizeProgress(newPos, newRect)
        
        # just absolute positioning for now (TEST)
        deltaPos = newPos - self.resizeOldPos
        deltaSize = newRect.size() - self.resizeOldRect.size()
        
        self.widget.setPosition(self.preResizePosition +
                                PyCEGUI.UVector2(PyCEGUI.UDim(0, deltaPos.x()), PyCEGUI.UDim(0, deltaPos.y())))
        self.widget.setSize(self.preResizeSize +
                            PyCEGUI.UVector2(PyCEGUI.UDim(0, deltaSize.width()), PyCEGUI.UDim(0, deltaSize.height())))
        
        for item in self.childItems():
            if isinstance(item, Manipulator):
                item.updateFromWidgetData()
        
    def notifyResizeFinished(self, newPos, newRect):
        super(Manipulator, self).notifyResizeFinished(newPos, newRect)
        
        self.updateFromWidgetData()
        
        for item in self.childItems():
            if isinstance(item, Manipulator):
                item.setVisible(True)

    def boundingClipPath(self):
        ret = QPainterPath()
        ret.addRect(self.boundingRect())
        
        return ret

    def isAboveItem(self, item):
        # undecidable otherwise
        assert(item.scene() == self.scene())
        
        # FIXME: nasty nasty way to do this
        for i in self.scene().items():
            if i is self:
                return True
            if i is item:
                return False
            
        assert(False)
        
    def paint(self, painter, option, widget):
        painter.save()
        
        clipPath = QPainterPath()
        clipPath.addRect(QRectF(-self.scenePos().x(), -self.scenePos().y(), self.scene().sceneRect().width(), self.scene().sceneRect().height()))
        for item in self.collidingItems():
            if isinstance(item, Manipulator):
                if item.isAboveItem(self):
                    clipPath = clipPath.subtracted(item.boundingClipPath().translated(item.scenePos() - self.scenePos()))
        
        painter.setClipPath(clipPath)
        
        super(Manipulator, self).paint(painter, option, widget)
        
        baseSize = self.widget.getParentPixelSize()
        if self.widget.getParent() is not None and not self.widget.isNonClientWindow():
            baseSize = self.widget.getParent().getUnclippedInnerRect().getSize()
        
        guidePenSize = 1
        
        if self.resizeInProgress or self.isAnyHandleSelected():
            # draw the size guides
            
            widgetSize = self.widget.getSize()
    
            relativeWidthInPixels = PyCEGUI.CoordConverter.asAbsolute(PyCEGUI.UDim(widgetSize.d_x.d_scale, 0), baseSize.d_width)
            absoluteWidthInPixels = widgetSize.d_x.d_offset
            
            widthStartPoint = self.rect().topLeft() - QPointF(0, 1 + guidePenSize)
            widthMidPoint = widthStartPoint + QPointF(relativeWidthInPixels, 0)
            widthEndPoint = widthMidPoint + QPointF(absoluteWidthInPixels, 0)
            widthAbsoluteOffset = QPointF(0, -guidePenSize) if relativeWidthInPixels * absoluteWidthInPixels < 0 else QPointF(0, 0)
            
            pen = QPen()
            pen.setWidth(guidePenSize)
            pen.setColor(QColor(255, 0, 0, 255))
            painter.setPen(pen)
            painter.drawLine(widthStartPoint, widthMidPoint)
            pen.setColor(QColor(0, 255, 0, 255))
            painter.setPen(pen)
            painter.drawLine(widthMidPoint + widthAbsoluteOffset, widthEndPoint + widthAbsoluteOffset)
            
            relativeHeightInPixels = PyCEGUI.CoordConverter.asAbsolute(PyCEGUI.UDim(widgetSize.d_y.d_scale, 0), baseSize.d_height)
            absoluteHeightInPixels = widgetSize.d_y.d_offset
            
            heightStartPoint = self.rect().topRight() + QPointF(1 + guidePenSize, 0)
            heightMidPoint = heightStartPoint + QPointF(0, relativeHeightInPixels)
            heightEndPoint = heightMidPoint + QPointF(0, absoluteHeightInPixels)
            heightAbsoluteOffset = QPointF(guidePenSize, 0) if relativeHeightInPixels * absoluteHeightInPixels < 0 else QPointF(0, 0)
            
            pen = QPen()
            pen.setWidth(guidePenSize)
            pen.setColor(QColor(255, 0, 0, 255))
            painter.setPen(pen)
            painter.drawLine(heightStartPoint, heightMidPoint)
            pen.setColor(QColor(0, 255, 0, 255))
            painter.setPen(pen)
            painter.drawLine(heightMidPoint + heightAbsoluteOffset, heightEndPoint + heightAbsoluteOffset)
            
        if self.isSelected() or self.resizeInProgress or self.isAnyHandleSelected():
            # draw the position guides
            widgetPosition = self.widget.getPosition()
            # we draw right to left and hopefully this will end at the origin
            
            absoluteXInPixels = widgetPosition.d_x.d_offset
            relativeXInPixels = PyCEGUI.CoordConverter.asAbsolute(PyCEGUI.UDim(widgetPosition.d_x.d_scale, 0), baseSize.d_width)
            
            xStartPoint = self.rect().topLeft()
            xMidPoint = xStartPoint - QPointF(absoluteXInPixels, 0)
            xEndPoint = xMidPoint - QPointF(relativeXInPixels, 0)
            xRelativeOffset = QPointF(0, guidePenSize) if relativeXInPixels * absoluteXInPixels < 0 else QPointF(0, 0)
            
            pen = QPen()
            pen.setWidth(guidePenSize)
            pen.setColor(QColor(0, 255, 0, 255))
            painter.setPen(pen)
            painter.drawLine(xStartPoint, xMidPoint)
            pen.setColor(QColor(255, 0, 0, 255))
            painter.setPen(pen)
            painter.drawLine(xMidPoint + xRelativeOffset, xEndPoint + xRelativeOffset)
            
            absoluteYInPixels = widgetPosition.d_y.d_offset
            relativeYInPixels = PyCEGUI.CoordConverter.asAbsolute(PyCEGUI.UDim(widgetPosition.d_y.d_scale, 0), baseSize.d_height)
            
            yStartPoint = self.rect().topLeft()
            yMidPoint = yStartPoint - QPointF(0, absoluteYInPixels)
            yEndPoint = yMidPoint - QPointF(0, relativeYInPixels)
            yRelativeOffset = QPointF(-guidePenSize, 0) if relativeYInPixels * absoluteYInPixels < 0 else QPointF(0, 0)
            
            pen = QPen()
            pen.setWidth(guidePenSize)
            pen.setColor(QColor(0, 255, 0, 255))
            painter.setPen(pen)
            painter.drawLine(yStartPoint, yMidPoint)
            pen.setColor(QColor(255, 0, 0, 255))
            painter.setPen(pen)
            painter.drawLine(yMidPoint + yRelativeOffset, yEndPoint + yRelativeOffset)
            
        painter.restore()
