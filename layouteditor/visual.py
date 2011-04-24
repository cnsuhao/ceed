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

import mixedtab
import propertysetinspector

import cegui
import PyCEGUI

import undo
import resizable

import ui.layouteditor.hierarchydockwidget
import ui.layouteditor.propertiesdockwidget
import ui.layouteditor.createwidgetdockwidget

class HierarchyDockWidget(QDockWidget):
    def __init__(self, parent):
        super(HierarchyDockWidget, self).__init__()
        
        self.parent = parent
        
        self.ui = ui.layouteditor.hierarchydockwidget.Ui_HierarchyDockWidget()
        self.ui.setupUi(self)
        
        self.tree = self.findChild(QTreeWidget, "tree")
        
        self.rootWidgetManipulator = None
        
    def getTreeItemForManipulator(self, manipulator):
        ret = QTreeWidgetItem([manipulator.widget.getName(), manipulator.widget.getType()])
        
        for item in manipulator.childItems():
            if isinstance(item, cegui.widget.Manipulator):
                childItem = self.getTreeItemForManipulator(item)
                ret.addChild(childItem)
                
        return ret
        
    def setRootWidgetManipulator(self, root):
        self.rootWidgetManipulator = root
        
        rootWidgetItem = self.getTreeItemForManipulator(root)
        self.tree.clear()
        self.tree.addTopLevelItem(rootWidgetItem)
        self.tree.expandAll()

class PropertiesDockWidget(QDockWidget):
    def __init__(self, parent):
        super(PropertiesDockWidget, self).__init__()
        
        self.parent = parent
        
        self.ui = ui.layouteditor.propertiesdockwidget.Ui_PropertiesDockWidget()
        self.ui.setupUi(self)
        
        self.inspector = self.findChild(propertysetinspector.PropertySetInspector, "inspector")

class CreateWidgetDockWidget(QDockWidget):
    def __init__(self, parent):
        super(CreateWidgetDockWidget, self).__init__()
        
        self.parent = parent
        
        self.ui = ui.layouteditor.createwidgetdockwidget.Ui_CreateWidgetDockWidget()
        self.ui.setupUi(self)
        
        self.tree = self.findChild(QTreeWidget, "tree")
        
    def populate(self):
        self.tree.clear()
        
        wl = self.parent.parent.mainWindow.ceguiContainerWidget.getAvailableWidgetsBySkin()
        
        for skin, widgets in wl.iteritems():
            skinItem = None
            
            if skin == "__no_skin__":
                skinItem = self.tree.invisibleRootItem()
            else:
                skinItem = QTreeWidgetItem()
                skinItem.setText(0, skin)
                self.tree.addTopLevelItem(skinItem)
                
            # skinItem now represents the skin node, we add all widgets in that skin to it
            
            for widget in widgets:
                widgetItem = QTreeWidgetItem()
                widgetItem.setText(0, widget)
                skinItem.addChild(widgetItem)

class EditingScene(cegui.widget.GraphicsScene):
    def __init__(self, parent):
        super(EditingScene, self).__init__()
        
        self.parent = parent
        self.rootManipulator = None
        
        self.selectionChanged.connect(self.slot_selectionChanged)
        
    def setRootWidget(self, widget):
        self.clear()
        
        self.rootManipulator = cegui.widget.Manipulator(widget)
        self.addItem(self.rootManipulator)
        
    def getWidgetManipulatorByPath(self, widgetPath):
        path = widgetPath.split("/", 1)
        assert(len(path) >= 1)
        
        if len(path) == 1:
            assert(path[0] == self.rootManipulator.widget.getName())
            
            return self.rootManipulator
        
        else:
            # path[1] is the remainder of the path
            return self.rootManipulator.getWidgetManipulatorByPath(path[1])
        
    def setSceneRect(self, rect):
        # overridden to keep the manipulators in sync
        
        super(EditingScene, self).setSceneRect(rect)
        
        if self.rootManipulator is not None:
            self.rootManipulator.updateFromWidget()
            
    def slot_selectionChanged(self):
        selection = self.selectedItems()
        
        sets = []
        for item in selection:
            if isinstance(item, cegui.widget.Manipulator):
                sets.append(item.widget)
            
        self.parent.propertiesDockWidget.inspector.setPropertySets(sets)
        
    def mouseReleaseEvent(self, event):
        super(EditingScene, self).mouseReleaseEvent(event)
        
        movedWidgetPaths = []
        movedOldPositions = {}
        movedNewPositions = {}
        
        resizedWidgetPaths = []
        resizedOldPositions = {}
        resizedOldSizes = {}
        resizedNewPositions = {}
        resizedNewSizes = {}
        
        # we have to "expand" the items, adding parents of resizing handles
        # instead of the handles themselves
        expandedSelectedItems = []
        for selectedItem in self.selectedItems():
            if isinstance(selectedItem, cegui.widget.Manipulator):
                expandedSelectedItems.append(selectedItem)
            elif isinstance(selectedItem, resizable.ResizingHandle):
                if isinstance(selectedItem.parentItem(), cegui.widget.Manipulator):
                    expandedSelectedItems.append(selectedItem.parentItem())
        
        for item in expandedSelectedItems:
            if isinstance(item, cegui.widget.Manipulator):
                if item.preMovePos is not None:
                    widgetPath = item.widget.getNamePath()
                    movedWidgetPaths.append(widgetPath)
                    movedOldPositions[widgetPath] = item.preMovePos
                    movedNewPositions[widgetPath] = item.widget.getPosition()
                    
                    # it won't be needed anymore so we use this to mark we picked this item up
                    item.preMovePos = None

                if item.preResizePos is not None and item.preResizeSize is not None:
                    widgetPath = item.widget.getNamePath()
                    resizedWidgetPaths.append(widgetPath)
                    resizedOldPositions[widgetPath] = item.preResizePos
                    resizedOldSizes[widgetPath] = item.preResizeSize
                    resizedNewPositions[widgetPath] = item.widget.getPosition()
                    resizedNewSizes[widgetPath] = item.widget.getSize()
                    
                    # it won't be needed anymore so we use this to mark we picked this item up
                    item.preResizePos = None
                    item.preResizeSize = None
        
        if len(movedWidgetPaths) > 0:
            cmd = undo.MoveCommand(self, movedWidgetPaths, movedOldPositions, movedNewPositions)
            self.parent.parent.undoStack.push(cmd)
            
        if len(resizedWidgetPaths) > 0:
            cmd = undo.ResizeCommand(self, resizedWidgetPaths, resizedOldPositions, resizedOldSizes, resizedNewPositions, resizedNewSizes)
            self.parent.parent.undoStack.push(cmd)

class VisualEditing(QWidget, mixedtab.EditMode):
    def __init__(self, parent):
        super(VisualEditing, self).__init__()
        
        self.parent = parent
        self.rootWidget = None
        
        self.hierarchyDockWidget = HierarchyDockWidget(self)
        self.propertiesDockWidget = PropertiesDockWidget(self)
        self.createWidgetDockWidget = CreateWidgetDockWidget(self)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
        self.scene = EditingScene(self)

    def initialise(self, rootWidget):
        self.replaceRootWidget(rootWidget)
        self.createWidgetDockWidget.populate()
    
    def replaceRootWidget(self, newRoot):
        oldRoot = self.rootWidget
            
        self.rootWidget = newRoot
        self.scene.setRootWidget(newRoot)
        self.hierarchyDockWidget.setRootWidgetManipulator(self.scene.rootManipulator)

        PyCEGUI.System.getSingleton().setGUISheet(self.rootWidget)
    
        if oldRoot:
            PyCEGUI.WindowManager.getSingleton().destroyWindow(oldRoot)
            
        # cause full redraw to ensure nothing gets stuck
        PyCEGUI.System.getSingleton().signalRedraw()
    
    def showEvent(self, event):
        self.parent.mainWindow.ceguiContainerWidget.activate(self, self.parent.filePath, self.scene)
        
        PyCEGUI.System.getSingleton().setGUISheet(self.rootWidget)

        self.hierarchyDockWidget.setEnabled(True)
        self.propertiesDockWidget.setEnabled(True)
        self.createWidgetDockWidget.setEnabled(True)

        super(VisualEditing, self).showEvent(event)
    
    def hideEvent(self, event):
        self.hierarchyDockWidget.setEnabled(False)
        self.propertiesDockWidget.setEnabled(False)
        self.createWidgetDockWidget.setEnabled(False)
        
        # this is sometimes called even before the parent is initialised
        if hasattr(self.parent, "mainWindow"):
            self.parent.mainWindow.ceguiContainerWidget.deactivate(self)
            
        super(VisualEditing, self).hideEvent(event)
    