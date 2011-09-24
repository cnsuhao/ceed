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
import cegui
import timeline

import ui.editors.animation_list.animationlistdockwidget
import ui.editors.animation_list.timelinedockwidget

class AnimationListDockWidget(QDockWidget):
    """Lists animations in the currently opened animation list XML
    """
    
    def __init__(self, visual):
        super(AnimationListDockWidget, self).__init__()
        
        self.visual = visual
        
        self.ui = ui.editors.animation_list.animationlistdockwidget.Ui_AnimationListDockWidget()
        self.ui.setupUi(self)
        
        self.list = self.findChild(QListWidget, "list")
        
class TimelineDockWidget(QDockWidget):
    """Shows a timeline of currently selected animation (from the animation list dock widget)
    """
    
    def __init__(self, visual):
        super(TimelineDockWidget, self).__init__()
        
        self.visual = visual
        
        self.ui = ui.editors.animation_list.timelinedockwidget.Ui_TimelineDockWidget()
        self.ui.setupUi(self)
        
        self.view = self.findChild(QGraphicsView, "view")
        self.scene = QGraphicsScene()
        self.timeline = timeline.AnimationTimeline()
        self.scene.addItem(self.timeline)

class EditingScene(cegui.widgethelpers.GraphicsScene):
    """This scene is used just to preview the animation in the state user selects.
    """
    
    def __init__(self, visual):
        super(EditingScene, self).__init__(mainwindow.MainWindow.instance.ceguiInstance)
        
        self.visual = visual

class VisualEditing(QWidget, editors.mixed.EditMode):
    """This is the default visual editing mode for animation lists
    
    see editors.mixed.EditMode
    """
    
    def __init__(self, tabbedEditor):
        super(VisualEditing, self).__init__()
        
        self.tabbedEditor = tabbedEditor
        
        self.animationListDockWidget = AnimationListDockWidget(self)
        self.timelineDockWidget = TimelineDockWidget(self)
        
        self.scene = EditingScene(self)

    def showEvent(self, event):
        mainwindow.MainWindow.instance.ceguiContainerWidget.activate(self, self.tabbedEditor.filePath, self.scene)
        mainwindow.MainWindow.instance.ceguiContainerWidget.setViewFeatures(wheelZoom = True,
                                                                            middleButtonScroll = True,
                                                                            continuousRendering = True)
        
        self.animationListDockWidget.setEnabled(True)
        self.timelineDockWidget.setEnabled(True)
        
        super(VisualEditing, self).showEvent(event)
    
    def hideEvent(self, event):
        self.animationListDockWidget.setEnabled(False)
        self.timelineDockWidget.setEnabled(False)
        
        mainwindow.MainWindow.instance.ceguiContainerWidget.deactivate(self)
        
        super(VisualEditing, self).hideEvent(event)

import mainwindow
