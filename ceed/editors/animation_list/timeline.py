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

import PyCEGUI

class TimecodeLabel(QGraphicsRectItem):
    """Simply displays time position labels depending on the zoom level
    """
    
    range = property(lambda self: self.rect().width(),
                     lambda self, value: self._setRange(value))
    
    def __init__(self, parentItem = None, keyFrame = None):
        super(TimecodeLabel, self).__init__(parentItem)
        
        self.range = 1
        
        self.setFlags(QGraphicsItem.ItemIsFocusable)
        
    def _setRange(self, range):
        assert(range > 0)
        
        self.setRect(QRectF(0, 0, range, 15))
        
    def paint(self, painter, option, widget = None):
        #super(TimecodeLabel, self).paint(painter, option, widget)
        
        painter.save()
        
        try:
            transform = painter.worldTransform()
            xScale = transform.m11()
            
            assert(xScale > 0)
            
            minLabelWidth = 50
            maxLabelsPerSecond = xScale / minLabelWidth
            
            timeLabels = {}
            
            ## {{{ http://code.activestate.com/recipes/66472/ (r1)
            def frange(start, end=None, inc=None):
                "A range function, that does accept float increments..."
            
                if end == None:
                    end = start + 0.0
                    start = 0.0
            
                if inc == None:
                    inc = 1.0
            
                L = []
                while 1:
                    next = start + len(L) * inc
                    if inc > 0 and next >= end:
                        break
                    elif inc < 0 and next <= end:
                        break
                    L.append(next)
                    
                return L
            ## end of http://code.activestate.com/recipes/66472/ }}}
            
            # always draw start and end
            timeLabels[0] = True
            timeLabels[self.range] = True
            
            if maxLabelsPerSecond >= 0.1:
                for i in frange(0, self.range, 10):
                    # 0, 10, 20, ...
                    timeLabels[i] = True
                    
            if maxLabelsPerSecond >= 0.2:
                for i in frange(0, self.range, 5):
                    # 0, 5, 10, ...
                    timeLabels[i] = True
                    
            if maxLabelsPerSecond >= 1.0:
                for i in frange(0, self.range):
                    # 0, 1, 2, ...
                    timeLabels[i] = True
                    
            if maxLabelsPerSecond >= 2.0:
                for i in frange(0, self.range, 0.5):
                    # 0, 0.5, 1.0, ...
                    timeLabels[i] = True
                    
            if maxLabelsPerSecond >= 10.0:
                for i in frange(0, self.range, 0.1):
                    # 0, 0.1, 0.2, ...
                    timeLabels[i] = True
            
            painter.scale(1.0 / xScale, 1)
            font = QFont()
            font.setPixelSize(8)
            painter.setFont(font)
            painter.setPen(QPen())
            
            for key, value in timeLabels.iteritems():
                if value:
                    painter.drawText(key * xScale - minLabelWidth * 0.5, 0, minLabelWidth, 10, Qt.AlignHCenter | Qt.AlignBottom, str(key))
                    painter.drawLine(QPointF(key * xScale, 10), QPointF(key * xScale, 15))
            
        finally:
            painter.restore()
        
class AffectorTimelineKeyFrame(QGraphicsRectItem):
    def __init__(self, parentItem = None, keyFrame = None):
        super(AffectorTimelineKeyFrame, self).__init__(parentItem)
        
        self.setFlags(QGraphicsItem.ItemIsSelectable |
                      QGraphicsItem.ItemIsMovable |
                      QGraphicsItem.ItemIgnoresTransformations |
                      QGraphicsItem.ItemSendsGeometryChanges)
        
        # the parts between keyframes are z-value 0 so this makes key frames always "stand out"
        self.setZValue(1)
        self.setRect(0, 0, 15, 20)
        
        palette = QApplication.palette()
        self.setBrush(QBrush(palette.color(QPalette.Normal, QPalette.Background)))
        
        self.setKeyFrame(keyFrame)
        
    def setKeyFrame(self, keyFrame):
        self.keyFrame = keyFrame
        
        self.refresh()
        
    def refresh(self):
        self.setPos(self.keyFrame.getPosition() if self.keyFrame is not None else 0, 0)
    
    def paint(self, painter, option, widget = None):
        super(AffectorTimelineKeyFrame, self).paint(painter, option, widget)
        
        palette = QApplication.palette()
        
        # draw the circle representing the keyframe
        painter.setPen(QPen())
        painter.setBrush(QBrush(palette.color(QPalette.Normal, QPalette.ButtonText)))
        painter.drawEllipse(QPointF(7.5, 12.5), 3, 3)
        
    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange:
            newPosition = QPointF()
            
            newPosition.setX(min(value.x(), self.keyFrame.getParent().getParent().getDuration()))
            # keep the Y constant, don't allow any vertical changes to keyframes!
            newPosition.setY(self.pos().y())
            
            self.keyFrame.moveToPosition(newPosition.x())
            self.parentItem().update()

            return newPosition
        
        return super(AffectorTimelineKeyFrame, self).itemChange(change, value)

class AffectorTimelineSection(QGraphicsRectItem):
    def __init__(self, parentItem = None, affector = None):
        super(AffectorTimelineSection, self).__init__(parentItem)
        
        self.setFlags(QGraphicsItem.ItemIsFocusable |
                      QGraphicsItem.ItemIsSelectable)
        
        self.setAffector(affector)
        
    def setAffector(self, affector):
        self.affector = affector
        
        self.refresh()

    def refresh(self):
        self.setRect(0, 0, self.parentItem().animation.getDuration(), 20)
        
        for item in self.childItems():
            # refcount drops and python should destroy that item
            self.scene().removeItem(item)
            
        if self.affector is None:
            return
        
        i = 0
        while i < self.affector.getNumKeyFrames():
            affectorTimelineKeyFrame = AffectorTimelineKeyFrame(parentItem = self,
                                                                keyFrame = self.affector.getKeyFrameAtIdx(i))
            
            # affector timeline key frame will refresh itself automatically to the right position
            # upon construction
            
            i += 1
            
    def paint(self, painter, option, widget = None):
        super(AffectorTimelineSection, self).paint(painter, option, widget)
        
        painter.save()
        
        try:
            transform = painter.worldTransform()
            xScale = transform.m11()
            
            painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            palette = QApplication.palette()
            
            if self.affector.getNumKeyFrames() == 0:
                return
            
            def drawArrow(x, y):
                painter.setPen(Qt.SolidLine)
                painter.drawLine(QPointF(x, y), QPointF(x - 3 / xScale, y - 3))
                painter.drawLine(QPointF(x, y), QPointF(x - 3 / xScale, y + 3))
            
            previousKeyFrame = self.affector.getKeyFrameAtIdx(0)
            i = 1
            while i < self.affector.getNumKeyFrames():
                keyFrame = self.affector.getKeyFrameAtIdx(i)
                
                # previousKeyFrame -------- line we will draw -------> keyFrame
                
                previousPosition = previousKeyFrame.getPosition()
                currentPosition = keyFrame.getPosition()
                lineStartPosition = min(previousPosition + 15 / xScale, currentPosition)
                
                span = currentPosition - previousPosition
                assert(span >= 0)
                
                if keyFrame.getProgression() == PyCEGUI.KeyFrame.P_Linear:
                    # just a straight line in this case
                    painter.setPen(Qt.DashLine)
                    painter.drawLine(QPointF(lineStartPosition, 11), QPointF(currentPosition, 11))
                    drawArrow(currentPosition, 11)
                    
                elif keyFrame.getProgression() == PyCEGUI.KeyFrame.P_QuadraticAccelerating:
                    path = QPainterPath()
                    path.moveTo(lineStartPosition, 17)
                    path.quadTo(previousPosition + span * 3/4, 20, currentPosition, 5)
                    painter.setPen(Qt.DashLine)
                    painter.drawPath(path)
                    
                    drawArrow(currentPosition, 5)
                    
                elif keyFrame.getProgression() == PyCEGUI.KeyFrame.P_QuadraticDecelerating:
                    
                    path = QPainterPath()
                    path.moveTo(lineStartPosition, 3)
                    path.quadTo(previousPosition + span * 3/4, 0, currentPosition, 15)
                    painter.setPen(Qt.DashLine)
                    painter.drawPath(path)
                    
                    drawArrow(currentPosition, 15)
                    
                elif keyFrame.getProgression() == PyCEGUI.KeyFrame.P_Discrete:
                    painter.setPen(Qt.DashLine)
                    painter.drawLine(QPointF(lineStartPosition, 17), QPointF(previousPosition + span / 2, 17))
                    painter.drawLine(QPointF(previousPosition + span / 2, 5), QPointF(previousPosition + span / 2, 17))
                    painter.drawLine(QPointF(previousPosition + span / 2, 5), QPointF(currentPosition, 5))
                    
                    drawArrow(currentPosition, 5)
                else:
                    # wrong progression?
                    assert(False)
                
                previousKeyFrame = keyFrame
                i += 1
                
        finally:
            painter.restore()

class AnimationTimeline(QGraphicsRectItem):
    """A timeline widget for just one CEGUI animation"""
    
    def __init__(self, parentItem = None, animation = None):
        super(AnimationTimeline, self).__init__(parentItem)
        
        self.setFlags(QGraphicsItem.ItemIsFocusable |
                      QGraphicsItem.ItemIsSelectable)
        
        self.setAnimation(animation)
        
    def setAnimation(self, animation):
        self.animation = animation
        
        self.refresh()
    
    def refresh(self):
        for item in self.childItems():
            # refcount drops and python should destroy that item
            item.setParentItem(None)
            
        if self.animation is None:
            return
            
        i = 0
        while i < self.animation.getNumAffectors():
            affectorTimelineSection = AffectorTimelineSection(parentItem = self,
                                                              affector = self.animation.getAffectorAtIdx(i))
            
            # FIXME: Make the height of affector timeline a setting entry
            affectorTimelineSection.setPos(0, i * 22)
            
            i += 1
            