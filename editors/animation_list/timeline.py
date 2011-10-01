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
            newPosition = value
            
            newPosition.setX(value.x())
            # keep the Y constant, don't allow any vertical changes to keyframes!
            newPosition.setY(self.pos().y())

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
            