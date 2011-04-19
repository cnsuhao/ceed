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
    
    def paintPositionXGuides(self, baseSize, painter, option, widget):
        widgetPosition = self.widget.getPosition()
        guidePenSize = 1
        
        scaleXInPixels = PyCEGUI.CoordConverter.asAbsolute(PyCEGUI.UDim(widgetPosition.d_x.d_scale, 0), baseSize.d_width)
        offsetXInPixels = widgetPosition.d_x.d_offset
        
        alignment = self.widget.getHorizontalAlignment()
        startPoint = 0
        if alignment == PyCEGUI.HorizontalAlignment.HA_LEFT:
            startPoint = (self.rect().topLeft() + self.rect().bottomLeft()) / 2
        elif alignment == PyCEGUI.HorizontalAlignment.HA_CENTRE:
            startPoint = self.rect().center()
        elif alignment == PyCEGUI.HorizontalAlignment.HA_RIGHT:
            startPoint = (self.rect().topRight() + self.rect().bottomRight()) / 2
        else:
            assert(False)
            
        midPoint = startPoint - QPointF(offsetXInPixels, 0)
        endPoint = midPoint - QPointF(scaleXInPixels, 0)
        offset = QPointF(0, guidePenSize) if scaleXInPixels * offsetXInPixels < 0 else QPointF(0, 0)
        
        pen = QPen()
        pen.setWidth(guidePenSize)
        pen.setColor(QColor(0, 255, 0, 255))
        painter.setPen(pen)
        painter.drawLine(startPoint, midPoint)
        pen.setColor(QColor(255, 0, 0, 255))
        painter.setPen(pen)
        painter.drawLine(midPoint + offset, endPoint + offset)
        
    def paintPositionYGuides(self, baseSize, painter, option, widget):
        widgetPosition = self.widget.getPosition()
        guidePenSize = 1
        
        scaleYInPixels = PyCEGUI.CoordConverter.asAbsolute(PyCEGUI.UDim(widgetPosition.d_y.d_scale, 0), baseSize.d_height)
        offsetYInPixels = widgetPosition.d_y.d_offset
        
        alignment = self.widget.getVerticalAlignment()
        startPoint = 0
        if alignment == PyCEGUI.VerticalAlignment.VA_TOP:
            startPoint = (self.rect().topLeft() + self.rect().topRight()) / 2
        elif alignment == PyCEGUI.VerticalAlignment.VA_CENTRE:
            startPoint = self.rect().center()
        elif alignment == PyCEGUI.VerticalAlignment.VA_BOTTOM:
            startPoint = (self.rect().bottomLeft() + self.rect().bottomRight()) / 2
        else:
            assert(False)
            
        midPoint = startPoint - QPointF(0, offsetYInPixels)
        endPoint = midPoint - QPointF(0, scaleYInPixels)
        offset = QPointF(guidePenSize, 0) if scaleYInPixels * offsetYInPixels < 0 else QPointF(0, 0)
        
        pen = QPen()
        pen.setWidth(guidePenSize)
        pen.setColor(QColor(0, 255, 0, 255))
        painter.setPen(pen)
        painter.drawLine(startPoint, midPoint)
        pen.setColor(QColor(255, 0, 0, 255))
        painter.setPen(pen)
        painter.drawLine(midPoint + offset, endPoint + offset)

    def paintWidthGuides(self, baseSize, painter, option, widget):
        widgetSize = self.widget.getSize()
        guidePenSize = 1
        
        scaleXInPixels = PyCEGUI.CoordConverter.asAbsolute(PyCEGUI.UDim(widgetSize.d_x.d_scale, 0), baseSize.d_width)
        offsetXInPixels = widgetSize.d_x.d_offset
        
        startPoint = (self.rect().topLeft() + self.rect().bottomLeft()) / 2
        midPoint = startPoint + QPointF(scaleXInPixels, 0)
        endPoint = midPoint + QPointF(offsetXInPixels, 0)
        offset = QPointF(0, guidePenSize) if scaleXInPixels * offsetXInPixels < 0 else QPointF(0, 0)
        
        pen = QPen()
        pen.setWidth(guidePenSize)
        pen.setStyle(Qt.DashLine)
        pen.setColor(QColor(255, 0, 0, 255))
        painter.setPen(pen)
        painter.drawLine(startPoint, midPoint)
        pen.setColor(QColor(0, 255, 0, 255))
        painter.setPen(pen)
        painter.drawLine(midPoint + offset, endPoint + offset)

    def paintHeightGuides(self, baseSize, painter, option, widget):
        widgetSize = self.widget.getSize()
        guidePenSize = 1
        
        scaleYInPixels = PyCEGUI.CoordConverter.asAbsolute(PyCEGUI.UDim(widgetSize.d_y.d_scale, 0), baseSize.d_height)
        offsetYInPixels = widgetSize.d_y.d_offset

        startPoint = (self.rect().topLeft() + self.rect().topRight()) / 2
        midPoint = startPoint + QPointF(0, scaleYInPixels)
        endPoint = midPoint + QPointF(0, offsetYInPixels)
        offset = QPointF(guidePenSize, 0) if scaleYInPixels * offsetYInPixels < 0 else QPointF(0, 0)
        
        pen = QPen()
        pen.setWidth(guidePenSize)
        pen.setStyle(Qt.DashLine)
        pen.setColor(QColor(255, 0, 0, 255))
        painter.setPen(pen)
        painter.drawLine(startPoint, midPoint)
        pen.setColor(QColor(0, 255, 0, 255))
        painter.setPen(pen)
        painter.drawLine(midPoint + offset, endPoint + offset)
            
    def paint(self, painter, option, widget):
        baseSize = self.widget.getParentPixelSize()
        if self.widget.getParent() is not None and not self.widget.isNonClientWindow():
            baseSize = self.widget.getParent().getUnclippedInnerRect().getSize()
        
        # We intentionally draw this without clipping to make guides always be visible and "on top"
        if self.isSelected() or self.resizeInProgress or self.isAnyHandleSelected():
            # draw the size guides
            self.paintWidthGuides(baseSize, painter, option, widget)
            self.paintHeightGuides(baseSize, painter, option, widget)
            
            # draw the position guides
            self.paintPositionXGuides(baseSize, painter, option, widget)
            self.paintPositionYGuides(baseSize, painter, option, widget)
        
        painter.save()
        
        clipPath = QPainterPath()
        clipPath.addRect(QRectF(-self.scenePos().x(), -self.scenePos().y(), self.scene().sceneRect().width(), self.scene().sceneRect().height()))
        for item in self.collidingItems():
            if isinstance(item, Manipulator):
                if item.isAboveItem(self):
                    clipPath = clipPath.subtracted(item.boundingClipPath().translated(item.scenePos() - self.scenePos()))
        
        # we clip using stencil buffers to prevent overlapping outlines appearing
        # FIXME: This could potentially get very slow for huge layouts
        painter.setClipPath(clipPath)
        
        super(Manipulator, self).paint(painter, option, widget)

        painter.restore()
