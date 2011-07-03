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
import propertysetinspector

import cegui.widgethelpers
import PyCEGUI

import undo
import widgethelpers

import resizable

import ui.editors.layout.propertiesdockwidget

class WidgetHierarchyTreeWidget(QTreeWidget):
    def __init__(self, parent = None):
        super(WidgetHierarchyTreeWidget, self).__init__(parent)

class HierarchyDockWidget(QDockWidget):
    def __init__(self, visual):
        super(HierarchyDockWidget, self).__init__()
        
        self.visual = visual
        
        self.ui = ui.editors.layout.hierarchydockwidget.Ui_HierarchyDockWidget()
        self.ui.setupUi(self)
        
        self.tree = self.findChild(WidgetHierarchyTreeWidget, "tree")
        self.ignoreSelectionChanges = False
        self.tree.itemSelectionChanged.connect(self.slot_itemSelectionChanged)
        
        self.rootWidgetManipulator = None
        
    def getTreeItemForManipulator(self, manipulator):
        ret = QTreeWidgetItem([manipulator.widget.getName(), manipulator.widget.getType()])
        ret.setFlags(Qt.ItemIsEnabled |
                     Qt.ItemIsSelectable |
                     Qt.ItemIsDropEnabled)
        
        # interlink them so we can react on selection changes
        ret.setData(0, Qt.UserRole, manipulator)
        manipulator.treeWidgetItem = ret
        
        for item in manipulator.childItems():
            if isinstance(item, widgethelpers.Manipulator):
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

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Delete:
            handled = self.visual.scene.deleteSelectedWidgets()
            
            if handled:
                return True
        
        return super(HierarchyDockWidget, self).keyReleaseEvent(event)  

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
        
        self.ui = ui.editors.layout.propertiesdockwidget.Ui_PropertiesDockWidget()
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

class WidgetTypeTreeWidget(QTreeWidget):
    def __init__(self, parent = None):
        super(WidgetTypeTreeWidget, self).__init__(parent)
        
        self.setDragEnabled(True)
        
    def setVisual(self, visual):
        self.visual = visual
        
    def startDrag(self, dropActions):
        # shamelessly stolen from CELE2 by Paul D Turner (GPLv3)
        
        item = self.currentItem()
        widgetType = item.text(0)
        
        if item.parent():
            look = item.parent().text(0)
        else:
            look = ""

        mimeData = QMimeData()
        
        mimeData.setData("application/x-cegui-widget-type", QByteArray(str(look + "/" + widgetType if look else widgetType)))

        pixmap = QPixmap(75,40)
        painter = QPainter(pixmap)
        painter.eraseRect(0, 0, 75, 40)
        painter.setBrush(Qt.DiagCrossPattern)
        painter.drawRect(0, 0, 74, 39)
        painter.end()
        
        drag = QDrag(self)
        drag.setMimeData(mimeData)
        drag.setPixmap(pixmap)
        drag.setHotSpot(QPoint(0, 0))

        drag.exec_(Qt.CopyAction)
        
    def viewportEvent(self, event):
        if event.type() == QEvent.ToolTip:
            # TODO: The big question is whether to reuse cached previews or always render them again.
            #       I always render them again for now to avoid all sorts of caching issues
            #       (when scheme/looknfeel editing is in place, etc...)
            
            item = self.itemAt(event.pos())
            
            if item is not None and item.childCount() == 0:
                skin = item.parent().text(0) if item.parent() is not None else "__no_skin__"
                widgetType = item.text(0)
                
                fullWidgetType = widgetType if skin == "__no_skin__" else "%s/%s" % (skin, widgetType)
                tooltipText = ""
                try:
                    if skin == "__no_skin__":
                        tooltipText = "Unskinned widgetType"
                        
                    elif widgetType == "TabButton":
                        tooltipText = "Can't render a preview as this is an auto widgetType, requires parent to be rendered."
                        
                    else:
                        ba = QByteArray()
                        buffer = QBuffer(ba)
                        buffer.open(QIODevice.WriteOnly)
                        
                        mainwindow.MainWindow.instance.ceguiInstance.getWidgetPreviewImage(fullWidgetType).save(buffer, "PNG")
                        
                        tooltipText = "<img src=\"data:image/png;base64,%s\" />" % (ba.toBase64())
            
                except:
                    tooltipText = "Couldn't render a widgetType preview..."
                    
                item.setToolTip(0, "<small>Drag to the layout to create!</small><br />%s" % (tooltipText))
                
        return super(WidgetTypeTreeWidget, self).viewportEvent(event)

class CreateWidgetDockWidget(QDockWidget):
    def __init__(self, visual):
        super(CreateWidgetDockWidget, self).__init__()
        
        self.visual = visual
        
        self.ui = ui.editors.layout.createwidgetdockwidget.Ui_CreateWidgetDockWidget()
        self.ui.setupUi(self)
        
        self.tree = self.findChild(WidgetTypeTreeWidget, "tree")
        self.tree.setVisual(visual)
        
    def populate(self):
        self.tree.clear()
        
        wl = mainwindow.MainWindow.instance.ceguiInstance.getAvailableWidgetsBySkin()
        
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

class EditingScene(cegui.widgethelpers.GraphicsScene):
    def __init__(self, visual):
        super(EditingScene, self).__init__(mainwindow.MainWindow.instance.ceguiInstance)
        
        self.visual = visual
        self.rootManipulator = None
        
        self.ignoreSelectionChanges = False
        self.selectionChanged.connect(self.slot_selectionChanged)

    def setRootWidgetManipulator(self, manipulator):
        self.clear()
        
        self.rootManipulator = manipulator
        
        if self.rootManipulator is not None:
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
        
    def setCEGUIDisplaySize(self, width, height, lazyUpdate = True):
        # overridden to keep the manipulators in sync
        
        super(EditingScene, self).setCEGUIDisplaySize(width, height, lazyUpdate)
        
        # FIXME: this won't do much with lazyUpdate = False
        if hasattr(self, "rootManipulator") and self.rootManipulator is not None:
            self.rootManipulator.updateFromWidget()
    
    def deleteSelectedWidgets(self):
        widgetPaths = []
        
        selection = self.selectedItems()
        for item in selection:
            if isinstance(item, widgethelpers.Manipulator):
                widgetPaths.append(item.widget.getNamePath())
                
        cmd = undo.DeleteCommand(self.visual, widgetPaths)
        self.visual.tabbedEditor.undoStack.push(cmd)
    
    def slot_selectionChanged(self):
        selection = self.selectedItems()
        
        sets = []
        for item in selection:
            wdt = None
            
            if isinstance(item, widgethelpers.Manipulator):
                wdt = item.widget
                
            elif isinstance(item, resizable.ResizingHandle):
                if isinstance(item.parentResizable, widgethelpers.Manipulator):
                    wdt = item.parentResizable.widget
                    
            if wdt is not None and wdt not in sets:
                sets.append(wdt)
            
        self.visual.propertiesDockWidget.inspector.setPropertySets(sets)
        
        # we always sync the properties dock widget, we only ignore the hierarchy synchro if told so
        if not self.ignoreSelectionChanges:
            self.visual.hierarchyDockWidget.ignoreSelectionChanges = True
            
            self.visual.hierarchyDockWidget.tree.clearSelection()
            for item in selection:
                if isinstance(item, widgethelpers.Manipulator):
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
            if isinstance(selectedItem, widgethelpers.Manipulator):
                expandedSelectedItems.append(selectedItem)
            elif isinstance(selectedItem, resizable.ResizingHandle):
                if isinstance(selectedItem.parentItem(), widgethelpers.Manipulator):
                    expandedSelectedItems.append(selectedItem.parentItem())
        
        for item in expandedSelectedItems:
            if isinstance(item, widgethelpers.Manipulator):
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

class VisualEditing(QWidget, editors.mixed.EditMode):
    def __init__(self, tabbedEditor):
        super(VisualEditing, self).__init__()
        
        self.tabbedEditor = tabbedEditor
        
        self.hierarchyDockWidget = HierarchyDockWidget(self)
        self.propertiesDockWidget = PropertiesDockWidget(self)
        self.createWidgetDockWidget = CreateWidgetDockWidget(self)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
        self.scene = EditingScene(self)
        
        self.setupActions()
        self.setupToolBar()

    def setupActions(self):
        self.zoomOriginalAction = QAction(QIcon("icons/layout_editing/zoom_original.png"), "Zoom original", self)
        self.zoomOriginalAction.triggered.connect(lambda: self.scene.views()[0].zoomOriginal())
        
        self.zoomInAction = QAction(QIcon("icons/layout_editing/zoom_in.png"), "Zoom in (mouse wheel)", self)
        self.zoomInAction.triggered.connect(lambda: self.scene.views()[0].zoomIn())
        
        self.zoomOutAction = QAction(QIcon("icons/layout_editing/zoom_out.png"), "Zoom out (mouse wheel)", self)
        self.zoomOutAction.triggered.connect(lambda: self.scene.views()[0].zoomOut())
        
    def setupToolBar(self):
        self.toolBar = QToolBar()
        
        self.toolBar.addSeparator() # ---------------------------
        self.toolBar.addAction(self.zoomOriginalAction)
        self.toolBar.addAction(self.zoomInAction)
        self.toolBar.addAction(self.zoomOutAction)

    def initialise(self, rootWidget):
        # FIXME: unreadable
        self.propertiesDockWidget.inspector.setPropertyInspectorManager(mainwindow.MainWindow.instance.project.propertyInspectorManager)
        
        self.setRootWidget(rootWidget)
        self.createWidgetDockWidget.populate()
    
    def getCurrentRootWidget(self):
        return self.scene.rootManipulator.widget if self.scene.rootManipulator is not None else None
    
    def setRootWidgetManipulator(self, manipulator):
        oldRoot = self.getCurrentRootWidget()
        
        self.scene.setRootWidgetManipulator(manipulator)
        self.hierarchyDockWidget.setRootWidgetManipulator(self.scene.rootManipulator)
        
        PyCEGUI.System.getSingleton().setGUISheet(self.getCurrentRootWidget())
    
        if oldRoot:
            PyCEGUI.WindowManager.getSingleton().destroyWindow(oldRoot)
            
        # cause full redraw to ensure nothing gets stuck
        PyCEGUI.System.getSingleton().signalRedraw()
    
    def setRootWidget(self, widget):
        if widget is None:
            self.setRootWidgetManipulator(None)
        
        else:
            self.setRootWidgetManipulator(widgethelpers.Manipulator(self, None, widget))
    
    def notifyWidgetManipulatorsAdded(self, manipulators):
        self.hierarchyDockWidget.refresh()
        
    def notifyWidgetManipulatorsRemoved(self, widgetPaths):
        """We are passing widget paths because manipulators might be destroyed at this point"""
        
        self.hierarchyDockWidget.refresh()
    
    def showEvent(self, event):
        mainwindow.MainWindow.instance.ceguiContainerWidget.activate(self, self.tabbedEditor.filePath, self.scene)
        mainwindow.MainWindow.instance.ceguiContainerWidget.setViewFeatures(wheelZoom = True, middleButtonScroll = True, continuousRendering = False)
        
        PyCEGUI.System.getSingleton().setGUISheet(self.getCurrentRootWidget())

        self.hierarchyDockWidget.setEnabled(True)
        self.propertiesDockWidget.setEnabled(True)
        self.createWidgetDockWidget.setEnabled(True)
        self.toolBar.setEnabled(True)

        # make sure all the manipulators are in sync to matter what
        # this is there mainly for the situation when you switch to live preview, then change resolution, then switch
        # back to visual editing and all manipulators are of different size than they should be
        if self.scene.rootManipulator is not None:
            self.scene.rootManipulator.updateFromWidget()

        super(VisualEditing, self).showEvent(event)
    
    def hideEvent(self, event):
        self.hierarchyDockWidget.setEnabled(False)
        self.propertiesDockWidget.setEnabled(False)
        self.createWidgetDockWidget.setEnabled(False)
        self.toolBar.setEnabled(False)
        
        mainwindow.MainWindow.instance.ceguiContainerWidget.deactivate(self)
            
        super(VisualEditing, self).hideEvent(event)

# needs to be at the end to sort circular deps
import ui.editors.layout.hierarchydockwidget
import ui.editors.layout.createwidgetdockwidget
    
# needs to be at the end, import to get the singleton
import mainwindow
