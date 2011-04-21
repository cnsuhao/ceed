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
                
        self.absoluteMode = False
        self.lastNewPos = None
        self.lastNewRect = None
                
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
    
    def getBaseSize(self):
        if self.widget.getParent() is not None and not self.widget.isNonClientWindow():
            return self.widget.getParent().getUnclippedInnerRect().getSize()
        
        else:
            return self.widget.getParentPixelSize()

    def notifyResizeStarted(self):
        super(Manipulator, self).notifyResizeStarted()
        
        self.preResizePosition = self.widget.getPosition()
        self.preResizeSize = self.widget.getSize()
        
        for item in self.childItems():
            if isinstance(item, Manipulator):
                item.setVisible(False)
    
    def notifyResizeProgress(self, newPos, newRect):
        super(Manipulator, self).notifyResizeProgress(newPos, newRect)
        
        # absolute pixel deltas
        pixelDeltaPos = newPos - self.resizeOldPos
        pixelDeltaSize = newRect.size() - self.resizeOldRect.size()
        
        deltaPos = None
        deltaSize = None
        
        if self.absoluteMode:
            deltaPos = PyCEGUI.UVector2(PyCEGUI.UDim(0, pixelDeltaPos.x()), PyCEGUI.UDim(0, pixelDeltaPos.y()))
            deltaSize = PyCEGUI.UVector2(PyCEGUI.UDim(0, pixelDeltaSize.width()), PyCEGUI.UDim(0, pixelDeltaSize.height()))
        
        else:
            baseSize = self.getBaseSize()
            
            deltaPos = PyCEGUI.UVector2(PyCEGUI.UDim(pixelDeltaPos.x() / baseSize.d_width, 0), PyCEGUI.UDim(pixelDeltaPos.y() / baseSize.d_height, 0))
            deltaSize = PyCEGUI.UVector2(PyCEGUI.UDim(pixelDeltaSize.width() / baseSize.d_width, 0), PyCEGUI.UDim(pixelDeltaSize.height() / baseSize.d_height, 0))
        
        self.widget.setPosition(self.preResizePosition + deltaPos)
        self.widget.setSize(self.preResizeSize + deltaSize)
        
        for item in self.childItems():
            if isinstance(item, Manipulator):
                item.updateFromWidgetData()
                
        self.lastNewPos = newPos
        self.lastNewRect = newRect
        
    def notifyResizeFinished(self, newPos, newRect):
        super(Manipulator, self).notifyResizeFinished(newPos, newRect)
        
        self.updateFromWidgetData()
        
        for item in self.childItems():
            if isinstance(item, Manipulator):
                item.setVisible(True)
                
        self.lastNewPos = None
        self.lastNewRect = None

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
    
    def paintHorizontalGuides(self, baseSize, painter, option, widget):
        widgetPosition = self.widget.getPosition()
        widgetSize = self.widget.getSize()
        
        # x coordinate
        scaleXInPixels = PyCEGUI.CoordConverter.asAbsolute(PyCEGUI.UDim(widgetPosition.d_x.d_scale, 0), baseSize.d_width)
        offsetXInPixels = widgetPosition.d_x.d_offset
        
        # width
        scaleWidthInPixels = PyCEGUI.CoordConverter.asAbsolute(PyCEGUI.UDim(widgetSize.d_x.d_scale, 0), baseSize.d_width)
        offsetWidthInPixels = widgetSize.d_x.d_offset
        
        hAlignment = self.widget.getHorizontalAlignment()
        startXPoint = 0
        if hAlignment == PyCEGUI.HorizontalAlignment.HA_LEFT:
            startXPoint = (self.rect().topLeft() + self.rect().bottomLeft()) / 2
        elif hAlignment == PyCEGUI.HorizontalAlignment.HA_CENTRE:
            startXPoint = self.rect().center()
        elif hAlignment == PyCEGUI.HorizontalAlignment.HA_RIGHT:
            startXPoint = (self.rect().topRight() + self.rect().bottomRight()) / 2
        else:
            assert(False)
            
        midXPoint = startXPoint - QPointF(offsetXInPixels, 0)
        endXPoint = midXPoint - QPointF(scaleXInPixels, 0)
        xOffset = QPointF(0, 1) if scaleXInPixels * offsetXInPixels < 0 else QPointF(0, 0)

        pen = QPen()
        pen.setWidth(1)
        pen.setColor(QColor(0, 255, 0, 255))
        painter.setPen(pen)
        painter.drawLine(startXPoint, midXPoint)
        pen.setColor(QColor(255, 0, 0, 255))
        painter.setPen(pen)
        painter.drawLine(midXPoint + xOffset, endXPoint + xOffset)
        
        vAlignment = self.widget.getVerticalAlignment()
        startWPoint = 0
        if vAlignment == PyCEGUI.VerticalAlignment.VA_TOP:
            startWPoint = self.rect().bottomLeft()
        elif vAlignment == PyCEGUI.VerticalAlignment.VA_CENTRE:
            startWPoint = self.rect().bottomLeft()
        elif vAlignment == PyCEGUI.VerticalAlignment.VA_BOTTOM:
            startWPoint = self.rect().topLeft()
        else:
            assert(False)

        midWPoint = startWPoint + QPointF(scaleWidthInPixels, 0)
        endWPoint = midWPoint + QPointF(offsetWidthInPixels, 0)
        # FIXME: epicly unreadable
        wOffset = QPointF(0, -1 if vAlignment == PyCEGUI.VerticalAlignment.VA_BOTTOM else 1) if scaleWidthInPixels * offsetWidthInPixels < 0 else QPointF(0, 0)
        
        pen = QPen()
        pen.setWidth(1)
        pen.setColor(QColor(255, 0, 0, 255))
        painter.setPen(pen)
        painter.drawLine(startWPoint, midWPoint)
        pen.setColor(QColor(0, 255, 0, 255))
        painter.setPen(pen)
        painter.drawLine(midWPoint + wOffset, endWPoint + wOffset)
        
    def paintVerticalGuides(self, baseSize, painter, option, widget):
        widgetPosition = self.widget.getPosition()
        widgetSize = self.widget.getSize()
        
        # y coordinate
        scaleYInPixels = PyCEGUI.CoordConverter.asAbsolute(PyCEGUI.UDim(widgetPosition.d_y.d_scale, 0), baseSize.d_height)
        offsetYInPixels = widgetPosition.d_y.d_offset
        
        # height
        scaleHeightInPixels = PyCEGUI.CoordConverter.asAbsolute(PyCEGUI.UDim(widgetSize.d_y.d_scale, 0), baseSize.d_height)
        offsetHeightInPixels = widgetSize.d_y.d_offset
        
        vAlignment = self.widget.getVerticalAlignment()
        startYPoint = 0
        if vAlignment == PyCEGUI.VerticalAlignment.VA_TOP:
            startYPoint = (self.rect().topLeft() + self.rect().topRight()) / 2
        elif vAlignment == PyCEGUI.VerticalAlignment.VA_CENTRE:
            startYPoint = self.rect().center()
        elif vAlignment == PyCEGUI.VerticalAlignment.VA_BOTTOM:
            startYPoint = (self.rect().bottomLeft() + self.rect().bottomRight()) / 2
        else:
            assert(False)
            
        midYPoint = startYPoint - QPointF(0, offsetYInPixels)
        endYPoint = midYPoint - QPointF(0, scaleYInPixels)
        yOffset = QPointF(1, 0) if scaleYInPixels * offsetYInPixels < 0 else QPointF(0, 0)

        pen = QPen()
        pen.setWidth(1)
        pen.setColor(QColor(0, 255, 0, 255))
        painter.setPen(pen)
        painter.drawLine(startYPoint, midYPoint)
        pen.setColor(QColor(255, 0, 0, 255))
        painter.setPen(pen)
        painter.drawLine(midYPoint + yOffset, endYPoint + yOffset)

        hAlignment = self.widget.getHorizontalAlignment()
        startHPoint = 0
        if hAlignment == PyCEGUI.HorizontalAlignment.HA_LEFT:
            startHPoint = self.rect().topRight()
        elif hAlignment == PyCEGUI.HorizontalAlignment.HA_CENTRE:
            startHPoint = self.rect().topRight()
        elif hAlignment == PyCEGUI.HorizontalAlignment.HA_RIGHT:
            startHPoint = self.rect().topLeft()
        else:
            assert(False)

        midHPoint = startHPoint + QPointF(0, scaleHeightInPixels)
        endHPoint = midHPoint + QPointF(0, offsetHeightInPixels)
        # FIXME: epicly unreadable
        hOffset = QPointF(-1 if hAlignment == PyCEGUI.HorizontalAlignment.HA_RIGHT else 1, 0) if scaleHeightInPixels * offsetHeightInPixels < 0 else QPointF(0, 0)
        
        pen = QPen()
        pen.setWidth(1)
        pen.setColor(QColor(255, 0, 0, 255))
        painter.setPen(pen)
        painter.drawLine(startHPoint, midHPoint)
        pen.setColor(QColor(0, 255, 0, 255))
        painter.setPen(pen)
        painter.drawLine(midHPoint + hOffset, endHPoint + hOffset)
    
    def keyPressEvent(self, event):
        super(Manipulator, self).keyPressEvent(event)
        
        if event.key() == Qt.Key_Control:
            self.absoluteMode = True
            
            # immediately update if possible
            if self.resizeInProgress and (self.lastNewPos is not None and self.lastNewRect is not None):
                self.notifyResizeProgress(self.lastNewPos, self.lastNewRect)
            
    def keyReleaseEvent(self, event):
        super(Manipulator, self).keyReleaseEvent(event)
        
        if event.key() == Qt.Key_Control:
            self.absoluteMode = False
            
            # immediately update if possible
            if self.resizeInProgress and (self.lastNewPos is not None and self.lastNewRect is not None):
                self.notifyResizeProgress(self.lastNewPos, self.lastNewRect)

    def paint(self, painter, option, widget):
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

        baseSize = self.getBaseSize()
        
        # We intentionally draw this without clipping to make guides always be visible and "on top"
        if self.isSelected() or self.resizeInProgress or self.isAnyHandleSelected():
            self.paintHorizontalGuides(baseSize, painter, option, widget)
            self.paintVerticalGuides(baseSize, painter, option, widget)
