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

import PyCEGUI

from ceed.editors import mixed
from ceed import cegui
from ceed.editors.animation_list import timeline

import ceed.ui.editors.animation_list.animationlistdockwidget
import ceed.ui.editors.animation_list.timelinedockwidget
import ceed.ui.editors.animation_list.visualediting

class AnimationListDockWidget(QDockWidget):
    """Lists animations in the currently opened animation list XML
    """
    
    def __init__(self, visual):
        super(AnimationListDockWidget, self).__init__()
        
        self.visual = visual
        
        self.ui = ceed.ui.editors.animation_list.animationlistdockwidget.Ui_AnimationListDockWidget()
        self.ui.setupUi(self)
        
        self.list = self.findChild(QListWidget, "list")
        
class TimelineDockWidget(QDockWidget):
    """Shows a timeline of currently selected animation (from the animation list dock widget)
    """
    
    def __init__(self, visual):
        super(TimelineDockWidget, self).__init__()
        
        self.visual = visual
        
        self.ui = ceed.ui.editors.animation_list.timelinedockwidget.Ui_TimelineDockWidget()
        self.ui.setupUi(self)
        
        self.view = self.findChild(QGraphicsView, "view")
        self.scene = QGraphicsScene()
        self.timeline = timeline.AnimationTimeline()
        self.scene.addItem(self.timeline)
        self.view.setScene(self.scene)
        
        self.playButton = self.findChild(QPushButton, "playButton")
        self.playButton.clicked.connect(lambda: self.timeline.play())
        self.pauseButton = self.findChild(QPushButton, "pauseButton")
        self.pauseButton.clicked.connect(lambda: self.timeline.pause())
        self.stopButton = self.findChild(QPushButton, "stopButton")
        self.stopButton.clicked.connect(lambda: self.timeline.stop())

class EditingScene(cegui.widgethelpers.GraphicsScene):
    """This scene is used just to preview the animation in the state user selects.
    """
    
    def __init__(self, visual):
        super(EditingScene, self).__init__(mainwindow.MainWindow.instance.ceguiInstance)
        
        self.visual = visual

class VisualEditing(QWidget, mixed.EditMode):
    """This is the default visual editing mode for animation lists
    
    see editors.mixed.EditMode
    """
    
    def __init__(self, tabbedEditor):
        super(VisualEditing, self).__init__()
        
        self.ui = ceed.ui.editors.animation_list.visualediting.Ui_VisualEditing()
        self.ui.setupUi(self)
        
        self.tabbedEditor = tabbedEditor
        
        self.animationListDockWidget = AnimationListDockWidget(self)
        self.timelineDockWidget = TimelineDockWidget(self)
        self.timelineDockWidget.timeline.timePositionChanged.connect(self.slot_timePositionChanged)
        
        self.currentAnimation = None
        self.currentAnimationInstance = None
        self.currentPreviewWidget = None
        
        self.setAnimation(None)
        
        self.rootPreviewWidget = PyCEGUI.WindowManager.getSingleton().createWindow("DefaultWindow", "RootPreviewWidget")
        
        self.previewWidgetSelector = self.findChild(QComboBox, "previewWidgetSelector")
        self.previewWidgetSelector.currentIndexChanged.connect(self.slot_previewWidgetSelectorChanged)
        self.populateWidgetSelector()
        self.ceguiPreview = self.findChild(QWidget, "ceguiPreview")
        
        layout = QVBoxLayout(self.ceguiPreview)
        layout.setContentsMargins(0, 0, 0, 0)
        self.ceguiPreview.setLayout(layout)        
        
        self.scene = EditingScene(self)
        
        ## TEMPORARY TEST CODE ##
        animation = PyCEGUI.AnimationManager.getSingleton().createAnimation("Test")
        animation.setDuration(10)
        affector = animation.createAffector("Alpha", "float")
        affector.createKeyFrame(0, "1.0")
        affector.createKeyFrame(5, "0.5", progression = PyCEGUI.KeyFrame.P_Discrete)
        affector.createKeyFrame(10, "1.0", progression = PyCEGUI.KeyFrame.P_QuadraticAccelerating)
        
        affector = animation.createAffector("Text", "String")
        affector.createKeyFrame(0, "1.0")
        affector.createKeyFrame(8, "0.5", progression = PyCEGUI.KeyFrame.P_QuadraticDecelerating)
        affector.createKeyFrame(9, "1.0")
        
        self.setAnimation(animation)
        ## END TEMPORARY CODE ##

    def showEvent(self, event):
        mainwindow.MainWindow.instance.ceguiContainerWidget.activate(self.ceguiPreview, self.tabbedEditor.filePath, self.scene)
        mainwindow.MainWindow.instance.ceguiContainerWidget.setViewFeatures(wheelZoom = True,
                                                                            middleButtonScroll = True,
                                                                            continuousRendering = True)
        
        PyCEGUI.System.getSingleton().setGUISheet(self.rootPreviewWidget)
        
        self.animationListDockWidget.setEnabled(True)
        self.timelineDockWidget.setEnabled(True)
        
        super(VisualEditing, self).showEvent(event)
    
    def hideEvent(self, event):
        self.animationListDockWidget.setEnabled(False)
        self.timelineDockWidget.setEnabled(False)
        
        mainwindow.MainWindow.instance.ceguiContainerWidget.deactivate(self.ceguiPreview)
        
        super(VisualEditing, self).hideEvent(event)

    def synchInstanceAndWidget(self):
        if self.currentAnimationInstance is None:
            return
        
        self.currentAnimationInstance.setTargetWindow(None)

        if self.currentPreviewWidget is None:
            return
        
        self.currentAnimationInstance.setTargetWindow(self.currentPreviewWidget)
        self.currentAnimationInstance.apply()

    def setAnimation(self, animation):
        """Set animation we want to edit"""
        
        self.currentAnimation = animation
        
        if self.currentAnimationInstance is not None:
            PyCEGUI.AnimationManager.getSingleton().destroyAnimationInstance(self.currentAnimationInstance)
            self.currentAnimationInstance = None

        if self.currentAnimation is not None:
            self.currentAnimationInstance = PyCEGUI.AnimationManager.getSingleton().instantiateAnimation(self.currentAnimation)
        
        self.timelineDockWidget.timeline.setAnimation(self.currentAnimation)
        
        self.synchInstanceAndWidget()
        
    def setPreviewWidget(self, widgetType):
        if self.currentPreviewWidget is not None:
            self.rootPreviewWidget.removeChild(self.currentPreviewWidget)
            PyCEGUI.WindowManager.getSingleton().destroyWindow(self.currentPreviewWidget)
            self.currentPreviewWidget = None
        
        if widgetType != "":
            try:
                self.currentPreviewWidget = PyCEGUI.WindowManager.getSingleton().createWindow(widgetType, "PreviewWidget")
                
            except Exception as ex:
                QMessageBox.warning(self, "Unable to comply!", "Your selected preview widget of type '%s' can't be used as a preview widget, error occured ('%s')." % (widgetType, ex))
                self.currentPreviewWidget = None
                self.synchInstanceAndWidget()
                return
            
            self.currentPreviewWidget.setPosition(PyCEGUI.UVector2(PyCEGUI.UDim(0.25, 0), PyCEGUI.UDim(0.25, 0)))
            self.currentPreviewWidget.setSize(PyCEGUI.USize(PyCEGUI.UDim(0.5, 0), PyCEGUI.UDim(0.5, 0)))
            self.rootPreviewWidget.addChild(self.currentPreviewWidget)
            
        self.synchInstanceAndWidget()  
        
    def populateWidgetSelector(self):
        self.previewWidgetSelector.clear()
        self.previewWidgetSelector.addItem("") # no preview
        self.previewWidgetSelector.setCurrentIndex(0) # select no preview
        
        widgetsBySkin = mainwindow.MainWindow.instance.ceguiInstance.getAvailableWidgetsBySkin()
        for skin, widgets in widgetsBySkin.iteritems():
            if skin == "__no_skin__":
                # pointless to preview animations with invisible widgets
                continue
            
            for widget in widgets:
                widgetType = "%s/%s" % (skin, widget)
                
                self.previewWidgetSelector.addItem(widgetType)

    def slot_previewWidgetSelectorChanged(self, index):
        widgetType = self.previewWidgetSelector.itemText(index)
        
        self.setPreviewWidget(widgetType)
        
    def slot_timePositionChanged(self, oldPosition, newPosition):
        # there is intentionally no undo/redo for this (it doesn't change content or context)
        
        self.currentAnimationInstance.setPosition(newPosition)
        self.currentAnimationInstance.apply()
        
from ceed import mainwindow
