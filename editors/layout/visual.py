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
import cPickle

class WidgetHierarchyItem(QStandardItem):
    def __init__(self, manipulator):
        self.manipulator = manipulator
        
        if manipulator is not None:
            super(WidgetHierarchyItem, self).__init__(manipulator.widget.getName())
            
            self.setToolTip("type: %s" % (manipulator.widget.getType()))
            
            # NOTE: We use widget path here because that's what QVariant can serialise and pass forth
            #       I have had weird segfaults when storing manipulator directly here, perhaps they
            #       are related to PySide, perhaps they were caused by my stupidity, we will never know!
            #self.setData(0, Qt.UserRole, manipulator)
            # interlink them so we can react on selection changes
            self.setData(manipulator.widget.getNamePath(), Qt.UserRole)
            manipulator.treeItem = self
        
        else:
            super(WidgetHierarchyItem, self).__init__("<No widget>")
        
        self.setFlags(Qt.ItemIsEnabled |
                      Qt.ItemIsSelectable |
                      Qt.ItemIsDropEnabled |
                      Qt.ItemIsDragEnabled)
        
    def clone(self):
        ret = WidgetHierarchyItem(self.manipulator)
        
        # PySide bug: PySide doesn't take ownership so we have to hack this around like this :-(
        #             hopefully this gets fixed.
        #
        #             NASTY NASTY NASTY
        #
        # TODO: This means that whenever you move project items around, you create leaks that exist
        #       for the entire time of execution of the app!
        # UPDATE: This got fixed in 1.0.3
        #         I will leave the workaround in place until that is the version in Ubuntu stable
        
        if hasattr(self, "returnedClones"):
            self.returnedClones.append(ret)
        else:
            self.returnedClones = [ret]
        
        return ret

class WidgetHierarchyTreeModel(QStandardItemModel):
    def __init__(self, dockWidget):
        super(WidgetHierarchyTreeModel, self).__init__()
        
        self.dockWidget = dockWidget
        self.setItemPrototype(WidgetHierarchyItem(None))
        
    def constructSubtree(self, manipulator):
        ret = WidgetHierarchyItem(manipulator)
        
        for item in manipulator.childItems():
            if isinstance(item, widgethelpers.Manipulator):
                childSubtree = self.constructSubtree(item)
                ret.appendRow(childSubtree)
        
        return ret
        
    def setRootManipulator(self, rootManipulator):
        self.clear()
        self.appendRow(self.constructSubtree(rootManipulator))

    def mimeData(self, indexes):
        # if the selection contains children of something that is also selected, we don't include that
        # (it doesn't make sense to move it anyways, it will be moved with its parent)
        
        def isChild(parent, potentialChild):
            i = 0
            # DFS, Qt doesn't have helper methods for this it seems to me :-/
            while i < parent.rowCount():
                child = parent.child(i)
                
                if child is potentialChild:
                    return True
                
                if isChild(child, potentialChild):
                    return True
                
            return False
        
        topItems = []
        
        for index in indexes:
            item = self.itemFromIndex(index)
            hasParent = False
            
            for parentIndex in indexes:
                if parentIndex is index:
                    continue
                
                potentialParent = self.itemFromIndex(parentIndex)
                
                if isChild(item, potentialParent):
                    hasParent = True
                    break
                
            if not hasParent:
                topItems.append(item)
                
        data = []
        for item in topItems:
            data.append(item.data(Qt.UserRole))
            
        ret = QMimeData()
        ret.setData("application/x-ceed-widget-paths", cPickle.dumps(data))
        
        return ret

    def mimeTypes(self):
        return ["application/x-ceed-widget-paths", "application/x-ceed-widget-type"]

    def dropMimeData(self, data, action, row, column, parent):
        if data.hasFormat("application/x-ceed-widget-paths"):
            # data.data(..).data() looks weird but is the correct thing!
            widgetPaths = cPickle.loads(data.data("application/x-ceed-widget-paths").data())
            targetWidgetPaths = []
            newParent = self.itemFromIndex(parent)
            
            for widgetPath in widgetPaths:
                widgetName = widgetPath[widgetPath.rfind("/") + 1:]
                targetWidgetPaths.append(newParent.data(Qt.UserRole) + "/" + widgetName)
                
            if action == Qt.MoveAction:
                cmd = undo.ReparentCommand(self.dockWidget.visual, widgetPaths, targetWidgetPaths)
                # FIXME: unreadable
                self.dockWidget.visual.tabbedEditor.undoStack.push(cmd)
        
                return True
            
            elif action == Qt.CopyAction:
                # FIXME: TODO
                return False
            
        elif data.hasFormat("application/x-ceed-widget-type"):
            widgetType = data.data("application/x-ceed-widget-type").data()
            parentItem = self.itemFromIndex(parent)
            parentManipulator = self.dockWidget.visual.scene.getWidgetManipulatorByPath(parentItem.data(Qt.UserRole))
            
            cmd = undo.CreateCommand(self.dockWidget.visual, parentItem.data(Qt.UserRole), widgetType, parentManipulator.getUniqueChildWidgetName(widgetType.rsplit("/", 1)[-1]))
            self.dockWidget.visual.tabbedEditor.undoStack.push(cmd)
            
            return True
        
        return False

class WidgetHierarchyTreeView(QTreeView):
    """The actual widget hierarchy tree widget - what a horrible name
    This is a Qt widget that does exactly the same as QTreeWidget for now,
    it is a placeholder that will be put to use once the need arises - and it will.
    """
    
    def __init__(self, parent = None):
        super(WidgetHierarchyTreeView, self).__init__(parent)
        
        self.dockWidget = None
    
    def selectionChanged(self, selected, deselected):
        """Synchronizes tree selection with scene selection.
        """
        
        super(WidgetHierarchyTreeView, self).selectionChanged(selected, deselected)

        # we are running synchronization the other way, this prevents infinite loops and recursion
        if self.dockWidget.ignoreSelectionChanges:
            return
        
        self.dockWidget.visual.scene.ignoreSelectionChanges = True
        
        for index in selected.indexes():
            item = self.model().itemFromIndex(index)
            
            if isinstance(item, WidgetHierarchyItem):
                manipulatorPath = item.data(Qt.UserRole)
                manipulator = None
                if manipulatorPath is not None:
                    manipulator = self.dockWidget.visual.scene.getWidgetManipulatorByPath(manipulatorPath)
                
                if manipulator is not None:
                    manipulator.setSelected(True)
                    
        for index in deselected.indexes():
            item = self.model().itemFromIndex(index)

            if isinstance(item, WidgetHierarchyItem):
                manipulatorPath = item.data(Qt.UserRole)
                manipulator = None
                if manipulatorPath is not None:
                    manipulator = self.dockWidget.visual.scene.getWidgetManipulatorByPath(manipulatorPath)
                
                if manipulator is not None:
                    manipulator.setSelected(False)
        
        self.dockWidget.visual.scene.ignoreSelectionChanges = False

class HierarchyDockWidget(QDockWidget):
    """Displays and manages the widget hierarchy. Contains the WidgetHierarchyTreeWidget.
    """
    
    def __init__(self, visual):
        super(HierarchyDockWidget, self).__init__()
        
        self.visual = visual
        
        self.ui = ui.editors.layout.hierarchydockwidget.Ui_HierarchyDockWidget()
        self.ui.setupUi(self)
                
        self.ignoreSelectionChanges = False

        self.model = WidgetHierarchyTreeModel(self)
        self.treeView = self.findChild(WidgetHierarchyTreeView, "treeView")
        self.treeView.dockWidget = self
        self.treeView.setModel(self.model)
        
        self.rootWidgetManipulator = None
        
    def setRootWidgetManipulator(self, root):
        """Sets the widget manipulator that is at the root of our observed hierarchy.
        Uses getTreeItemForManipulator to recursively populate the tree.
        """
        
        self.rootWidgetManipulator = root
        self.model.setRootManipulator(root)
        self.treeView.expandAll()
        
    def refresh(self):
        """Refreshes the entire hierarchy completely from scratch"""
        
        self.setRootWidgetManipulator(self.rootWidgetManipulator)

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Delete:
            handled = self.visual.scene.deleteSelectedWidgets()
            
            if handled:
                return True
        
        return super(HierarchyDockWidget, self).keyReleaseEvent(event)

class PropertiesDockWidget(QDockWidget):
    """Lists and allows editing of properties of the selected widget(s). Uses the PropertySetInspector machinery.
    """
    
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
                
        # make sure to redraw the scene to preview the property
        self.visual.scene.update()
    
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
        
        # make sure to redraw the scene so the changes are visible    
        self.visual.scene.update()

class WidgetTypeTreeWidget(QTreeWidget):
    """Represents a single available widget for creation (it has a mapping in the scheme or is
    a stock special widget - like DefaultWindow).
    
    Also provides previews for the widgets
    """
    
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
        
        mimeData.setData("application/x-ceed-widget-type", QByteArray(str(look + "/" + widgetType if look else widgetType)))

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
    """This lists available widgets you can create and allows their creation (by drag N drop)
    """
    
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
    """This scene contains all the manipulators users want to interact it. You can visualise it as the
    visual editing centre screen where CEGUI is rendered.
    
    It renders CEGUI on it's background and outlines (via Manipulators) in front of it.
    """
    
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
                
        if len(widgetPaths) > 0:
            cmd = undo.DeleteCommand(self.visual, widgetPaths)
            self.visual.tabbedEditor.undoStack.push(cmd)
            
    def alignSelectionHorizontally(self, alignment):
        widgetPaths = []
        oldAlignments = {}
        
        selection = self.selectedItems()
        for item in selection:
            if isinstance(item, widgethelpers.Manipulator):
                widgetPath = item.widget.getNamePath()
                widgetPaths.append(widgetPath)
                oldAlignments[widgetPath] = item.widget.getHorizontalAlignment()
        
        if len(widgetPaths) > 0:        
            cmd = undo.HorizontalAlignCommand(self.visual, widgetPaths, oldAlignments, alignment)
            self.visual.tabbedEditor.undoStack.push(cmd)
        
    def alignSelectionVertically(self, alignment):
        widgetPaths = []
        oldAlignments = {}
        
        selection = self.selectedItems()
        for item in selection:
            if isinstance(item, widgethelpers.Manipulator):
                widgetPath = item.widget.getNamePath()
                widgetPaths.append(widgetPath)
                oldAlignments[widgetPath] = item.widget.getVerticalAlignment()
        
        if len(widgetPaths) > 0:        
            cmd = undo.VerticalAlignCommand(self.visual, widgetPaths, oldAlignments, alignment)
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
            
            self.visual.hierarchyDockWidget.treeView.clearSelection()
            for item in selection:
                if isinstance(item, widgethelpers.Manipulator):
                    if hasattr(item, "treeItem") and item.treeItem is not None:
                        self.visual.hierarchyDockWidget.treeView.selectionModel().select(item.treeItem.index(), QItemSelectionModel.Select)
            
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
    """This is the default visual editing mode
    
    see editors.mixed.EditMode
    """
    
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
        
        # horizontal alignment actions
        self.alignHLeftAction = QAction(QIcon("icons/layout_editing/align_hleft.png"), "Align left (horizontal)", self)
        self.alignHLeftAction.triggered.connect(lambda: self.scene.alignSelectionHorizontally(PyCEGUI.HA_LEFT))
        self.alignHCentreAction = QAction(QIcon("icons/layout_editing/align_hcentre.png"), "Align centre (horizontal)", self)
        self.alignHCentreAction.triggered.connect(lambda: self.scene.alignSelectionHorizontally(PyCEGUI.HA_CENTRE))
        self.alignHRightAction = QAction(QIcon("icons/layout_editing/align_hright.png"), "Align right (horizontal)", self)
        self.alignHRightAction.triggered.connect(lambda: self.scene.alignSelectionHorizontally(PyCEGUI.HA_RIGHT))
        
        # vertical alignment actions
        self.alignVTopAction = QAction(QIcon("icons/layout_editing/align_vtop.png"), "Align top (vertical)", self)
        self.alignVTopAction.triggered.connect(lambda: self.scene.alignSelectionVertically(PyCEGUI.VA_TOP))
        self.alignVCentreAction = QAction(QIcon("icons/layout_editing/align_vcentre.png"), "Align centre (vertical)", self)
        self.alignVCentreAction.triggered.connect(lambda: self.scene.alignSelectionVertically(PyCEGUI.VA_CENTRE))
        self.alignVBottomAction = QAction(QIcon("icons/layout_editing/align_vbottom.png"), "Align bottom (vertical)", self)
        self.alignVBottomAction.triggered.connect(lambda: self.scene.alignSelectionVertically(PyCEGUI.VA_BOTTOM))
        
        self.deleteAction = QAction(QIcon("icons/layout_editing/delete.png"), "Delete selection", self)
        self.deleteAction.triggered.connect(lambda: self.scene.deleteSelectedWidgets())
        
    def setupToolBar(self):
        self.toolBar = QToolBar()
        self.toolBar.setIconSize(QSize(32, 32))
        
        self.toolBar.addSeparator() # ---------------------------
        self.toolBar.addAction(self.zoomOriginalAction)
        self.toolBar.addAction(self.zoomInAction)
        self.toolBar.addAction(self.zoomOutAction)
        
        self.toolBar.addSeparator() # ---------------------------
        self.toolBar.addAction(self.alignHLeftAction)
        self.toolBar.addAction(self.alignHCentreAction)
        self.toolBar.addAction(self.alignHRightAction)
        self.toolBar.addSeparator() # ---------------------------
        self.toolBar.addAction(self.alignVTopAction)
        self.toolBar.addAction(self.alignVCentreAction)
        self.toolBar.addAction(self.alignVBottomAction)
        self.toolBar.addSeparator() # ---------------------------
        self.toolBar.addAction(self.deleteAction)

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
        """Sets the root widget we want to edit
        """
        
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

    def performCut(self):
        ret = self.performCopy()
        self.scene.deleteSelectedWidgets()
        
        return ret
    
    def performCopy(self):
        topMostSelected = []
        
        for item in self.scene.selectedItems():
            if not isinstance(item, widgethelpers.Manipulator):
                continue
            
            hasAncestorSelected = False
            
            for item2 in self.scene.selectedItems():
                if not isinstance(item2, widgethelpers.Manipulator):
                    continue
                
                if item is item2:
                    continue
                
                if item2.isAncestorOf(item):
                    hasAncestorSelected = True
                    break
    
            if not hasAncestorSelected:
                topMostSelected.append(item)
                
        if len(topMostSelected) == 0:
            return False
        
        # now we serialise the top most selected widgets (and thus their entire hierarchies)
        topMostSerialisationData = []
        for wdt in topMostSelected:
            serialisationData = widgethelpers.SerialisationData(self, wdt.widget)
            # we set the visual to None because we can't pickle QWidgets (also it would prevent copying across editors)
            # we will set it to the correct visual when we will be pasting it back
            serialisationData.setVisual(None)
            
            topMostSerialisationData.append(serialisationData)
            
        data = QMimeData()
        data.setData("application/x-ceed-widget-hierarchy-list", QByteArray(cPickle.dumps(topMostSerialisationData)))
        QApplication.clipboard().setMimeData(data)
    
        return True
    
    def performPaste(self):
        data = QApplication.clipboard().mimeData()
        
        if not data.hasFormat("application/x-ceed-widget-hierarchy-list"):
            return False
        
        topMostSerialisationData = cPickle.loads(data.data("application/x-ceed-widget-hierarchy-list").data())
        
        if len(topMostSerialisationData) == 0:
            return False
        
        targetManipulator = None
        for item in self.scene.selectedItems():
            if not isinstance(item, widgethelpers.Manipulator):
                continue
            
            # multiple targets, we can't decide!
            if targetManipulator is not None:
                return False
            
            targetManipulator = item
        
        for serialisationData in topMostSerialisationData:
            serialisationData.setVisual(self)
        
        cmd = undo.PasteCommand(self, topMostSerialisationData, targetManipulator.widget.getNamePath())
        self.tabbedEditor.undoStack.push(cmd)
        
        return True

# needs to be at the end to sort circular deps
import ui.editors.layout.hierarchydockwidget
import ui.editors.layout.createwidgetdockwidget
    
# needs to be at the end, import to get the singleton
import mainwindow
