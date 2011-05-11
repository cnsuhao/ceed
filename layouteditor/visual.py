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
    def __init__(self, visual):
        super(HierarchyDockWidget, self).__init__()
        
        self.visual = visual
        
        self.ui = ui.layouteditor.hierarchydockwidget.Ui_HierarchyDockWidget()
        self.ui.setupUi(self)
        
        self.tree = self.findChild(QTreeWidget, "tree")
        self.ignoreSelectionChanges = False
        self.tree.itemSelectionChanged.connect(self.slot_itemSelectionChanged)
        
        self.rootWidgetManipulator = None
        
    def getTreeItemForManipulator(self, manipulator):
        ret = QTreeWidgetItem([manipulator.widget.getName(), manipulator.widget.getType()])
        
        # interlink them so we can react on selection changes
        ret.setData(0, Qt.UserRole, manipulator)
        manipulator.treeWidgetItem = ret
        
        for item in manipulator.childItems():
            if isinstance(item, cegui.widget.Manipulator):
                childItem = self.getTreeItemForManipulator(item)
                ret.addChild(childItem)
                
        return ret
        
    def setRootWidgetManipulator(self, root):
        self.rootWidgetManipulator = root
        
        self.tree.clear()
        if root is not None:
            rootWidgetItem = self.getTreeItemForManipulator(root)
            self.tree.addTopLevelItem(rootWidgetItem)
            self.tree.expandAll()
        
    def refresh(self):
        self.setRootWidgetManipulator(self.rootWidgetManipulator)

    def slot_itemSelectionChanged(self):
        # todo: This method is really inefficient
        if self.ignoreSelectionChanges:
            return
        
        # AFAIK there is no better way to do this than this abomination
        def collectTreeWidgetItems(root):
            ret = []
            ret.append(root)
            
            i = 0
            while i < root.childCount():
                ret.extend(collectTreeWidgetItems(root.child(i)))
                i += 1
            
            return ret
    
        allItems = collectTreeWidgetItems(self.tree.invisibleRootItem())
        selection = self.tree.selectedItems()
        
        self.visual.scene.ignoreSelectionChanges = True
        self.visual.scene.clearSelection()
        
        for item in allItems:
            manipulator = item.data(0, Qt.UserRole)
            
            if manipulator is not None:
                for selected in selection:
                    if item is selected:
                        manipulator.setSelected(True)
                        break
        
        self.visual.scene.ignoreSelectionChanges = False

class PropertiesDockWidget(QDockWidget):
    def __init__(self, visual):
        super(PropertiesDockWidget, self).__init__()
        
        self.visual = visual
        
        self.ui = ui.layouteditor.propertiesdockwidget.Ui_PropertiesDockWidget()
        self.ui.setupUi(self)
        
        self.inspector = self.findChild(propertysetinspector.PropertySetInspector, "inspector")
        self.inspector.propertyEditingProgress.connect(self.slot_propertyEditingProgress)
        self.inspector.propertyEditingEnded.connect(self.slot_propertyEditingEnded)
        
    def slot_propertyEditingProgress(self, propertyName, value):
        # instant preview
        for set in self.inspector.propertySets:
            if set.isPropertyPresent(propertyName):
                set.setProperty(propertyName, value)
    
    def slot_propertyEditingEnded(self, propertyName, oldValues, value):
        widgetPaths = []
        undoOldValues = {}
        
        # set the properties where applicable
        for set in self.inspector.propertySets:
            if set.isPropertyPresent(propertyName):
                # the undo command will do this again anyways
                #set.setProperty(propertyName, value)
                
                if oldValues[set] != value:
                    widgetPath = set.getNamePath()
                    widgetPaths.append(widgetPath)
                    undoOldValues[widgetPath] = oldValues[set]
        
        if len(widgetPaths) > 0:        
            cmd = undo.PropertyEditCommand(self.visual, propertyName, widgetPaths, undoOldValues, value)
            # FIXME: unreadable
            self.visual.tabbedEditor.undoStack.push(cmd)

class CreateWidgetDockWidget(QDockWidget):
    def __init__(self, visual):
        super(CreateWidgetDockWidget, self).__init__()
        
        self.visual = visual
        
        self.ui = ui.layouteditor.createwidgetdockwidget.Ui_CreateWidgetDockWidget()
        self.ui.setupUi(self)
        
        self.tree = self.findChild(QTreeWidget, "tree")
        
    def populate(self):
        self.tree.clear()
        
        wl = mainwindow.MainWindow.instance.ceguiContainerWidget.getAvailableWidgetsBySkin()
        
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
    def __init__(self, visual):
        super(EditingScene, self).__init__()
        
        self.visual = visual
        self.rootManipulator = None
        
        self.ignoreSelectionChanges = False
        self.selectionChanged.connect(self.slot_selectionChanged)
        
    def setRootWidget(self, widget):
        self.clear()
        
        self.rootManipulator = cegui.widget.Manipulator(None, widget)
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
            
    def deleteSelectedWidgets(self):
        widgetPaths = []
        
        selection = self.selectedItems()
        for item in selection:
            if isinstance(item, cegui.widget.Manipulator):
                widgetPaths.append(item.widget.getNamePath())
                
        cmd = undo.DeleteCommand(self.visual, widgetPaths)
        self.visual.tabbedEditor.undoStack.push(cmd)
    
    def slot_selectionChanged(self):
        selection = self.selectedItems()
        
        sets = []
        for item in selection:
            widget = None
            
            if isinstance(item, cegui.widget.Manipulator):
                widget = item.widget
                
            elif isinstance(item, resizable.ResizingHandle):
                if isinstance(item.parentResizable, cegui.widget.Manipulator):
                    widget = item.parentResizable.widget
                    
            if widget is not None and widget not in sets:
                sets.append(widget)
            
        self.visual.propertiesDockWidget.inspector.setPropertySets(sets)
        
        # we always sync the properties dock widget, we only ignore the hierarchy synchro if told so
        if not self.ignoreSelectionChanges:
            self.visual.hierarchyDockWidget.ignoreSelectionChanges = True
            
            self.visual.hierarchyDockWidget.tree.clearSelection()
            for item in selection:
                if isinstance(item, cegui.widget.Manipulator):
                    if hasattr(item, "treeWidgetItem") and item.treeWidgetItem is not None:
                        item.treeWidgetItem.setSelected(True)
        
            self.visual.hierarchyDockWidget.ignoreSelectionChanges = False
        
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
            cmd = undo.MoveCommand(self.visual, movedWidgetPaths, movedOldPositions, movedNewPositions)
            self.visual.tabbedEditor.undoStack.push(cmd)
            
        if len(resizedWidgetPaths) > 0:
            cmd = undo.ResizeCommand(self.visual, resizedWidgetPaths, resizedOldPositions, resizedOldSizes, resizedNewPositions, resizedNewSizes)
            self.visual.tabbedEditor.undoStack.push(cmd)
            
    def keyReleaseEvent(self, event):
        handled = False
        
        if event.key() == Qt.Key_Delete:
            handled = self.deleteSelectedWidgets()           
            
        if not handled:
            super(EditingScene, self).keyReleaseEvent(event)
            
        else:
            event.accept()

class VisualEditing(QWidget, mixedtab.EditMode):
    def __init__(self, tabbedEditor):
        super(VisualEditing, self).__init__()
        
        self.tabbedEditor = tabbedEditor
        self.rootWidget = None
        
        self.hierarchyDockWidget = HierarchyDockWidget(self)
        self.propertiesDockWidget = PropertiesDockWidget(self)
        self.createWidgetDockWidget = CreateWidgetDockWidget(self)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
        self.scene = EditingScene(self)

    def initialise(self, rootWidget):
        # FIXME: unreadable
        self.propertiesDockWidget.inspector.setPropertyInspectorManager(mainwindow.MainWindow.instance.project.propertyInspectorManager)
        
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
        mainwindow.MainWindow.instance.ceguiContainerWidget.activate(self, self.tabbedEditor.filePath, self.scene)
        
        PyCEGUI.System.getSingleton().setGUISheet(self.rootWidget)

        self.hierarchyDockWidget.setEnabled(True)
        self.propertiesDockWidget.setEnabled(True)
        self.createWidgetDockWidget.setEnabled(True)

        super(VisualEditing, self).showEvent(event)
    
    def hideEvent(self, event):
        self.hierarchyDockWidget.setEnabled(False)
        self.propertiesDockWidget.setEnabled(False)
        self.createWidgetDockWidget.setEnabled(False)
        
        mainwindow.MainWindow.instance.ceguiContainerWidget.deactivate(self)
            
        super(VisualEditing, self).hideEvent(event)
    
# needs to be at the end, import to get the singleton
import mainwindow
