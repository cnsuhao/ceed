##############################################################################
#   CEED - Unified CEGUI asset editor
#
#   Copyright (C) 2011-2012   Martin Preisler <martin@preisler.me>
#                             and contributing authors (see AUTHORS file)
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
##############################################################################

from collections import OrderedDict

from PySide import QtCore
from PySide import QtGui
import cPickle
import os

import PyCEGUI

from ceed import resizable

from ceed.editors import multi

from ceed.cegui import widgethelpers as cegui_widgethelpers

from ceed.editors.looknfeel import undo
from ceed.editors.looknfeel import widgethelpers

from ceed.propertysetinspector import PropertyInspectorWidget
from ceed.propertysetinspector import CEGUIWidgetLookPropertiesManager

import ceed.propertytree as pt

from ceed.propertytree.editors import PropertyEditorRegistry


class LookNFeelVisualEditing(QtGui.QWidget, multi.EditMode):
    """This is the default visual editing mode

    see ceed.editors.multi.EditMode
    """

    def __init__(self, tabbedEditor):
        """
        :param tabbedEditor: LookNFeelTabbedEditor
        :return:
        """
        super(LookNFeelVisualEditing, self).__init__()

        self.tabbedEditor = tabbedEditor

        self.lookNFeelHierarchyDockWidget = LookNFeelHierarchyDockWidget(self)
        self.lookNFeelWidgetLookSelectorWidget = LookNFeelWidgetLookSelectorWidget(self, tabbedEditor)
        self.lookNFeelPropertyEditorDockWidget = LookNFeelPropertyEditorDockWidget(self, tabbedEditor)

        looknfeel = QtGui.QVBoxLayout(self)
        looknfeel.setContentsMargins(0, 0, 0, 0)
        self.setLayout(looknfeel)

        self.scene = EditingScene(self)

        self.setupActions()
        self.setupToolBar()
        self.lookNFeelHierarchyDockWidget.treeView.setupContextMenu()

    def destroy(self):
        rootWidget = self.getCurrentRootWidget()

        # Remove the widget with the previous WidgetLook from the scene
        while rootWidget.getChildCount() != 0:
            PyCEGUI.WindowManager.getSingleton().destroyWindow(rootWidget.getChildAtIdx(0))

        # TODO (Ident) :
        # Fix this in CEGUI default and remove it later in the CEED default branch
        # for more info see: http://cegui.org.uk/wiki/The_Lederhosen_project_-_The_Second_Coming
        PyCEGUI.WindowManager.getSingleton().cleanDeadPool()

    def setupActions(self):
        self.connectionGroup = action.ConnectionGroup(action.ActionManager.instance)

    def setupToolBar(self):
        self.toolBar = QtGui.QToolBar("looknfeel")
        self.toolBar.setObjectName("looknfeelToolbar")
        self.toolBar.setIconSize(QtCore.QSize(32, 32))

    def rebuildEditorMenu(self, editorMenu):
        """Adds actions to the editor menu"""
        # similar to the toolbar, includes the focus filter box action

    def initialise(self):
        propertyMap = mainwindow.MainWindow.instance.project.propertyMap
        widgetLookPropertyManager = CEGUIWidgetLookPropertyManager(propertyMap, self)
        self.lookNFeelPropertyEditorDockWidget.inspector.setPropertyManager(widgetLookPropertyManager)

        rootWidget = PyCEGUI.WindowManager.getSingleton().createWindow("DefaultWindow", "LookNFeelEditorRoot")
        self.setRootWidget(rootWidget)

    def displayNewTargetWidgetLook(self):
        rootWidget = self.getCurrentRootWidget()

        # Remove the widget with the previous WidgetLook from the scene
        while rootWidget.getChildCount() != 0:
            PyCEGUI.WindowManager.getSingleton().destroyWindow(rootWidget.getChildAtIdx(0))

        # TODO (Ident) :
        # Fix this in CEGUI default and remove it later in the CEED default branch
        # for more info see: http://cegui.org.uk/wiki/The_Lederhosen_project_-_The_Second_Coming
        PyCEGUI.WindowManager.getSingleton().cleanDeadPool()

        # Add new widget representing the new WidgetLook to the scene
        widgetLookWindow = PyCEGUI.WindowManager.getSingleton().createWindow(self.tabbedEditor.targetWidgetLook, "WidgetLookWindow")
        rootWidget.addChild(widgetLookWindow)

        #Refresh the drawing of the preview
        self.scene.update()

    def getCurrentRootWidget(self):
        return self.scene.rootManipulator.widget if self.scene.rootManipulator is not None else None

    def setRootWidgetManipulator(self, manipulator):
        oldRoot = self.getCurrentRootWidget()

        self.scene.setRootWidgetManipulator(manipulator)
        self.lookNFeelHierarchyDockWidget.setRootWidgetManipulator(self.scene.rootManipulator)

        PyCEGUI.System.getSingleton().getDefaultGUIContext().setRootWindow(self.getCurrentRootWidget())

        if oldRoot:
            PyCEGUI.WindowManager.getSingleton().destroyWindow(oldRoot)

        # cause full redraw of the default GUI context to ensure nothing gets stuck
        PyCEGUI.System.getSingleton().getDefaultGUIContext().markAsDirty()

    def setRootWidget(self, widget):
        """Sets the root widget we want to edit
        """
        self.setRootWidgetManipulator(widgethelpers.Manipulator(self, None, widget))

    def notifyWidgetManipulatorsAdded(self, manipulators):
        self.lookNFeelHierarchyDockWidget.refresh()

    def notifyWidgetManipulatorsRemoved(self, widgetPaths):
        """We are passing widget paths because manipulators might be destroyed at this point"""

        self.lookNFeelHierarchyDockWidget.refresh()

    def showEvent(self, event):
        mainwindow.MainWindow.instance.ceguiContainerWidget.activate(self, self.scene)
        mainwindow.MainWindow.instance.ceguiContainerWidget.setViewFeatures(wheelZoom = True,
                                                                            middleButtonScroll = True,
                                                                            continuousRendering = settings.getEntry("looknfeel/visual/continuous_rendering").value)

        PyCEGUI.System.getSingleton().getDefaultGUIContext().setRootWindow(self.getCurrentRootWidget())

        self.lookNFeelHierarchyDockWidget.setEnabled(True)
        self.lookNFeelWidgetLookSelectorWidget.setEnabled(True)
        self.lookNFeelPropertyEditorDockWidget.setEnabled(True)

        self.toolBar.setEnabled(True)
        if self.tabbedEditor.editorMenu() is not None:
            self.tabbedEditor.editorMenu().menuAction().setEnabled(True)

        # make sure all the manipulators are in sync to matter what
        # this is there mainly for the situation when you switch to live preview, then change resolution, then switch
        # back to visual editing and all manipulators are of different size than they should be
        if self.scene.rootManipulator is not None:
            self.scene.rootManipulator.updateFromWidget()

        # connect all our actions
        self.connectionGroup.connectAll()

        super(LookNFeelVisualEditing, self).showEvent(event)

    def hideEvent(self, event):
        # disconnected all our actions
        self.connectionGroup.disconnectAll()

        self.lookNFeelHierarchyDockWidget.setEnabled(False)
        self.lookNFeelWidgetLookSelectorWidget.setEnabled(False)
        self.lookNFeelPropertyEditorDockWidget.setEnabled(False)

        self.toolBar.setEnabled(False)
        if self.tabbedEditor.editorMenu() is not None:
            self.tabbedEditor.editorMenu().menuAction().setEnabled(False)

        mainwindow.MainWindow.instance.ceguiContainerWidget.deactivate(self)

        super(LookNFeelVisualEditing, self).hideEvent(event)

    def focusPropertyInspectorFilterBox(self):
        """Focuses into property set inspector filter

        This potentially allows the user to just press a shortcut to find properties to edit,
        instead of having to reach for a mouse.
        """

        filterBox = self.propertiesDockWidget.inspector.filterBox
        # selects all contents of the filter so that user can replace that with their search phrase
        filterBox.selectAll()
        # sets focus so that typing puts text into the filter box without clicking
        filterBox.setFocus()

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

        data = QtCore.QMimeData()
        data.setData("application/x-ceed-widget-hierarchy-list", QtCore.QByteArray(cPickle.dumps(topMostSerialisationData)))
        QtGui.QApplication.clipboard().setMimeData(data)

        return True

    def performPaste(self):
        data = QtGui.QApplication.clipboard().mimeData()

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

        if targetManipulator is None:
            return False

        for serialisationData in topMostSerialisationData:
            serialisationData.setVisual(self)

        cmd = undo.PasteCommand(self, topMostSerialisationData, targetManipulator.widget.getNamePath())
        self.tabbedEditor.undoStack.push(cmd)

        # select the topmost pasted widgets for convenience
        self.scene.clearSelection()
        for serialisationData in topMostSerialisationData:
            manipulator = targetManipulator.getManipulatorByPath(serialisationData.name)
            manipulator.setSelected(True)

        return True

    def performDelete(self):
        return self.scene.deleteSelectedWidgets()


class LookNFeelWidgetLookSelectorWidget(QtGui.QDockWidget):
    """This dock widget allows to select a WidgetLook from a combobox and start editing it
    """

    def __init__(self, visual, tabbedEditor):
        """
        :param visual: LookNFeelVisualEditing
        :param tabbedEditor: LookNFeelTabbedEditor
        :return:
        """
        super(LookNFeelWidgetLookSelectorWidget, self).__init__()

        self.tabbedEditor = tabbedEditor

        self.visual = visual

        self.ui = ceed.ui.editors.looknfeel.looknfeelwidgetlookselectorwidget.Ui_LookNFeelWidgetLookSelector()
        self.ui.setupUi(self)

        self.fileNameLabel = self.findChild(QtGui.QLabel, "fileNameLabel")
        """:type : QtGui.QLabel"""
        self.setFileNameLabel()

        self.widgetLookNameBox = self.findChild(QtGui.QComboBox, "widgetLookNameBox")
        """:type : QtGui.QComboBox"""

        self.editWidgetLookButton = self.findChild(QtGui.QPushButton, "editWidgetLookButton")
        self.editWidgetLookButton.pressed.connect(self.slot_editWidgetLookButtonPressed)

    def slot_editWidgetLookButtonPressed(self):
        # Handles the actions necessary after a user selects a new WidgetLook to edit
        selectedItemIndex = self.widgetLookNameBox.currentIndex()
        selectedWidgetLookName = self.widgetLookNameBox.itemData(selectedItemIndex)

        command = undo.TargetWidgetChangeCommand(self.visual, self.tabbedEditor, selectedWidgetLookName)
        self.tabbedEditor.undoStack.push(command)

    def populateWidgetLookComboBox(self, widgetLookNameTuples):
        self.widgetLookNameBox.clear
        # We populate the combobox with items that use the original name as display text but have the name of the live-editable WidgetLook stored as a QVariant

        for nameTuple in widgetLookNameTuples:
            self.widgetLookNameBox.addItem(nameTuple[0], nameTuple[1])

    def setFileNameLabel(self):
        # Shortens the file name so that it fits into the label and ends with "...", the full path is set as a tooltip
        fileNameStr = self.tabbedEditor.filePath
        fontMetrics = self.fileNameLabel.fontMetrics()
        labelWidth = self.fileNameLabel.minimumSize().width()
        fontMetricsWidth = fontMetrics.width(fileNameStr)
        if labelWidth < fontMetricsWidth:
            self.fileNameLabel.setText(fontMetrics.elidedText(fileNameStr, QtCore.Qt.ElideRight, labelWidth))
        else:
            self.fileNameLabel.setText(fileNameStr)

        self.fileNameLabel.setToolTip(fileNameStr)


class LookNFeelPropertyEditorDockWidget(QtGui.QDockWidget):
    """This dock widget allows to add, remove or edit the Property, PropertyDefinition and PropertyLinkDefinition elements of a WidgetLook
    """

    def __init__(self, visual, tabbedEditor):
        """
        :param visual: LookNFeelVisualEditing
        :param tabbedEditor: LookNFeelTabbedEditor
        :return:
        """
        super(LookNFeelPropertyEditorDockWidget, self).__init__()
        self.setObjectName("WidgetLookPropertiesDockWidget")
        self.visual = visual

        self.setWindowTitle("WidgetLook Properties")
        # Make the dock take as much space as it can vertically
        self.setSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Maximum)

        self.inspector = PropertyInspectorWidget()
        self.inspector.ptree.setupRegistry(PropertyEditorRegistry(True))

        self.setWidget(self.inspector)


class CEGUIWidgetLookPropertyManager(CEGUIWidgetLookPropertiesManager):
    """Customises the CEGUIPropertyManager by binding to a 'visual'
    so it can manipulate the widgets via undo commands.

    It also customises the sorting of the categories.
    """

    def __init__(self, propertyMap, visual):
        super(CEGUIWidgetLookPropertyManager, self).__init__(propertyMap)
        self.visual = visual

    def createProperty(self, ceguiProperty, ceguiSets):
        prop = super(CEGUIWidgetLookPropertyManager, self).createProperty(ceguiProperty, ceguiSets, WidgetMultiPropertyWrapper)
        prop.ceguiProperty = ceguiProperty
        prop.ceguiSets = ceguiSets
        prop.visual = self.visual

        return prop

    def buildCategories(self, source):
        categories = super(CEGUIWidgetLookPropertyManager, self).buildCategories(source)

        # sort categories by name but keep some special categories on top
        def getSortKey(t):
            name, _  = t

            if name == "Element":
                return "000Element"
            elif name == "NamedElement":
                return "001NamedElement"
            elif name == "Window":
                return "002Window"
            elif name.startswith("CEGUI/"):
                return name[6:]
            elif name == "Unknown":
                return "ZZZUnknown"
            else:
                return name

        categories = OrderedDict(sorted(categories.items(), key=getSortKey))

        return categories



class LookNFeelHierarchyItem(QtGui.QStandardItem):
    def __init__(self, manipulator):
        self.manipulator = manipulator

        if manipulator is not None:
            super(LookNFeelHierarchyItem, self).__init__(manipulator.widget.getName())

            self.setToolTip("type: %s" % (manipulator.widget.getType()))

            # NOTE: We use widget path here because that's what QVariant can serialise and pass forth
            #       I have had weird segfaults when storing manipulator directly here, perhaps they
            #       are related to PySide, perhaps they were caused by my stupidity, we will never know!
            #self.setData(0, Qt.UserRole, manipulator)
            # interlink them so we can react on selection changes
            self.setData(manipulator.widget.getNamePath(), QtCore.Qt.UserRole)
            manipulator.treeItem = self

        else:
            super(LookNFeelHierarchyItem, self).__init__("<No Look n' Feel element>")

        self.setFlags(QtCore.Qt.ItemIsEnabled |
                      QtCore.Qt.ItemIsSelectable |
                      QtCore.Qt.ItemIsEditable |
                      QtCore.Qt.ItemIsDropEnabled |
                      QtCore.Qt.ItemIsDragEnabled |
                      QtCore.Qt.ItemIsUserCheckable)

        self.setData(QtCore.Qt.Unchecked, QtCore.Qt.CheckStateRole)

    def clone(self):
        ret = LookNFeelHierarchyItem(self.manipulator)
        ret.setData(self.data(QtCore.Qt.CheckStateRole), QtCore.Qt.CheckStateRole)
        return ret

    def refreshPathData(self, recursive = True):
        """Updates the stored path data for the item and its children
        """

        if self.manipulator is not None:
            self.setText(self.manipulator.widget.getName())
            self.setData(self.manipulator.widget.getNamePath(), QtCore.Qt.UserRole)

            if recursive:
                for i in range(self.rowCount()):
                    self.child(i).refreshPathData()

    def setData(self, value, role):
        if role == QtCore.Qt.CheckStateRole and self.manipulator is not None:
            # synchronise the manipulator with the lock state
            self.manipulator.setLocked(value == QtCore.Qt.Checked)

        return super(LookNFeelHierarchyItem, self).setData(value, role)

    def setLocked(self, locked, recursive = False):
        """Locks or unlocks this item.

        locked - if True this item gets locked = user won't be able to move it
                 in the visual editing mode.
        recursive - if True, all children of this item will also get affected
                    They will get locked or unlocked depending on the "locked"
                    argument, independent of their previous lock state.
        """

        # we do it this way around to make sure the checkbox's check state
        # is always up to date
        self.setData(QtCore.Qt.Checked if locked else QtCore.Qt.Unchecked,
                     QtCore.Qt.CheckStateRole)

        if recursive:
            for i in range(self.rowCount()):
                child = self.child(i)
                child.setLocked(locked, True)


class LookNFeelHierarchyTreeModel(QtGui.QStandardItemModel):
    def __init__(self, dockWidget):
        super(LookNFeelHierarchyTreeModel, self).__init__()

        self.dockWidget = dockWidget
        self.setItemPrototype(LookNFeelHierarchyItem(None))

    def data(self, index, role = QtCore.Qt.DisplayRole):
        return super(LookNFeelHierarchyTreeModel, self).data(index, role)

    def setData(self, index, value, role = QtCore.Qt.EditRole):
        if role == QtCore.Qt.EditRole:
            item = self.itemFromIndex(index)

            # if the new name is the same, cancel
            if value == item.manipulator.widget.getName():
                return False

            # return false because the undo command has changed the text of the item already
            return False

        return super(LookNFeelHierarchyTreeModel, self).setData(index, value, role)

    def flags(self, index):
        return super(LookNFeelHierarchyTreeModel, self).flags(index)

    def shouldManipulatorBeSkipped(self, manipulator):
        return \
           manipulator.widget.isAutoWindow() and \
           settings.getEntry("looknfeel/visual/hide_deadend_autowidgets").value and \
           not manipulator.hasNonAutoWidgetDescendants()

    def constructSubtree(self, manipulator):
        ret = LookNFeelHierarchyItem(manipulator)

        manipulatorChildren = []

        for item in manipulator.childItems():
            if isinstance(item, widgethelpers.Manipulator):
                manipulatorChildren.append(item)

        manipulatorChildren = sorted(manipulatorChildren, key = lambda item: item.getWidgetPath())

        for item in manipulatorChildren:
            if self.shouldManipulatorBeSkipped(item):
                # skip this branch as per settings
                continue

            childSubtree = self.constructSubtree(item)
            ret.appendRow(childSubtree)

        return ret

    def synchroniseSubtree(self, hierarchyItem, manipulator, recursive = True):
        """Attempts to synchronise subtree with given widget manipulator.
        If such a thing isn't possible it returns False.

        recursive - If True the synchronisation will recurse, trying to
                    unify child widget hierarchy items with child manipulators.
                    (This is generally what you want to do)
        """

        if hierarchyItem is None or manipulator is None:
            # no manipulator = no hierarchy item, we definitely can't synchronise
            return False

        if hierarchyItem.manipulator is not manipulator:
            # this widget hierarchy item itself will need to be recreated
            return False

        hierarchyItem.refreshPathData(False)

        if recursive:
            manipulatorsToRecreate = manipulator.getChildManipulators()

            i = 0
            # we knowingly do NOT use range in here, the rowCount might change
            # while we are processing!
            while i < hierarchyItem.rowCount():
                childHierarchyItem = hierarchyItem.child(i)

                if childHierarchyItem.manipulator in manipulatorsToRecreate and \
                   self.synchroniseSubtree(childHierarchyItem, childHierarchyItem.manipulator, True):
                    manipulatorsToRecreate.remove(childHierarchyItem.manipulator)
                    i += 1

                else:
                    hierarchyItem.removeRow(i)

            for childManipulator in manipulatorsToRecreate:
                if self.shouldManipulatorBeSkipped(childManipulator):
                    # skip this branch as per settings
                    continue

                hierarchyItem.appendRow(self.constructSubtree(childManipulator))

        return True

    def getRootHierarchyItem(self):
        if self.rowCount() > 0:
            return self.item(0)

        else:
            return None

    def setRootManipulator(self, rootManipulator):
        if not self.synchroniseSubtree(self.getRootHierarchyItem(), rootManipulator):
            self.clear()

            if rootManipulator is not None:
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

                i += 1

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
            data.append(item.data(QtCore.Qt.UserRole))

        ret = QtCore.QMimeData()
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
            if newParent is None:
                return False

            newParentManipulator = self.dockWidget.visual.scene.getManipulatorByPath(newParent.data(QtCore.Qt.UserRole))

            usedNames = set()
            for widgetPath in widgetPaths:
                oldWidgetName = widgetPath[widgetPath.rfind("/") + 1:]
                # Prevent name clashes at the new parent
                # When a name clash occurs, we suggest a new name to the user and
                # ask them to confirm it/enter their own.
                # The tricky part is that we have to consider the other widget renames
                # too (in case we're reparenting and renaming more than one widget)
                # and we must prevent invalid names (i.e. containing "/")
                suggestedName = oldWidgetName
                while True:
                    # get a name that's not used in the new parent, trying to keep
                    # the suggested name (which is the same as the old widget name at
                    # the beginning)
                    tempName = newParentManipulator.getUniqueChildWidgetName(suggestedName)
                    # if the name we got is the same as the one we wanted...
                    if tempName == suggestedName:
                        # ...we need to check our own usedNames list too, in case
                        # another widget we're reparenting has got this name.
                        counter = 2
                        while suggestedName in usedNames:
                            # When this happens, we simply add a numeric suffix to
                            # the suggested name. The result could theoretically
                            # collide in the new parent but it's OK because this
                            # is just a suggestion and will be checked again when
                            # the 'while' loops.
                            suggestedName = tempName + str(counter)
                            counter += 1
                            error = "Widget name is in use by another widget being " + ("copied" if action == QtCore.Qt.CopyAction else "moved")

                        # if we had no collision, we can keep this name!
                        if counter == 2:
                            break
                    else:
                        # The new parent had a child with that name already and so
                        # it gave us a new suggested name.
                        suggestedName = tempName
                        error = "Widget name already exists in the new parent"

                    # Ask the user to confirm our suggested name or enter a new one
                    # We do this in a loop because we validate the user input
                    while True:
                        suggestedName, ok = QtGui.QInputDialog.getText(
                                            self.dockWidget,
                                            error,
                                            "New name for '" + oldWidgetName + "':",
                                            QtGui.QLineEdit.Normal,
                                            suggestedName)
                        # Abort everything if the user cancels the dialog
                        if not ok:
                            return False
                        # Validate the entered name
                        suggestedName = widgethelpers.Manipulator.getValidWidgetName(suggestedName)
                        if suggestedName:
                            break
                        error = "Invalid name, please try again"

                usedNames.add(suggestedName)
                targetWidgetPaths.append(newParent.data(QtCore.Qt.UserRole) + "/" + suggestedName)

            if action == QtCore.Qt.MoveAction:
                #cmd = undo.ReparentCommand(self.dockWidget.visual, widgetPaths, targetWidgetPaths)
                # FIXME: unreadable
                #self.dockWidget.visual.tabbedEditor.undoStack.push(cmd)

                return True

            elif action == QtCore.Qt.CopyAction:
                # FIXME: TODO
                return False

        elif data.hasFormat("application/x-ceed-widget-type"):
            widgetType = data.data("application/x-ceed-widget-type").data()
            parentItem = self.itemFromIndex(parent)
            # if the drop was at empty space (parentItem is None) the parentItemPath
            # should be "" if no root item exists, otherwise the name of the root item
            parentItemPath = parentItem.data(QtCore.Qt.UserRole) if parentItem is not None else self.dockWidget.visual.scene.rootManipulator.widget.getName() if self.dockWidget.visual.scene.rootManipulator is not None else ""
            parentManipulator = self.dockWidget.visual.scene.getManipulatorByPath(parentItemPath) if parentItemPath else None
            uniqueName = parentManipulator.getUniqueChildWidgetName(widgetType.rsplit("/", 1)[-1]) if parentManipulator is not None else widgetType.rsplit("/", 1)[-1]

            #cmd = undo.CreateCommand(self.dockWidget.visual, parentItemPath, widgetType, uniqueName)
            #self.dockWidget.visual.tabbedEditor.undoStack.push(cmd)

            return True

        return False


class LookNFeelHierarchyTreeView(QtGui.QTreeView):
    """The actual widget hierarchy tree widget - what a horrible name
    This is a Qt widget that does exactly the same as QTreeWidget for now,
    it is a placeholder that will be put to use once the need arises - and it will.
    """

    def __init__(self, parent = None):
        super(LookNFeelHierarchyTreeView, self).__init__(parent)

        self.dockWidget = None

    def selectionChanged(self, selected, deselected):
        """Synchronizes tree selection with scene selection.
        """

        super(LookNFeelHierarchyTreeView, self).selectionChanged(selected, deselected)

        # we are running synchronization the other way, this prevents infinite loops and recursion
        if self.dockWidget.ignoreSelectionChanges:
            return

        self.dockWidget.visual.scene.ignoreSelectionChanges = True

        for index in selected.indexes():
            item = self.model().itemFromIndex(index)

            if isinstance(item, LookNFeelHierarchyItem):
                manipulatorPath = item.data(QtCore.Qt.UserRole)
                manipulator = None
                if manipulatorPath is not None:
                    manipulator = self.dockWidget.visual.scene.getManipulatorByPath(manipulatorPath)

                if manipulator is not None:
                    manipulator.setSelected(True)

        for index in deselected.indexes():
            item = self.model().itemFromIndex(index)

            if isinstance(item, LookNFeelHierarchyItem):
                manipulatorPath = item.data(QtCore.Qt.UserRole)
                manipulator = None
                if manipulatorPath is not None:
                    manipulator = self.dockWidget.visual.scene.getManipulatorByPath(manipulatorPath)

                if manipulator is not None:
                    manipulator.setSelected(False)

        self.dockWidget.visual.scene.ignoreSelectionChanges = False

    def setupContextMenu(self):
        self.setContextMenuPolicy(QtCore.Qt.DefaultContextMenu)

        self.contextMenu = QtGui.QMenu(self)

        self.renameAction = action.getAction("looknfeel/rename")
        self.contextMenu.addAction(self.renameAction)

        self.contextMenu.addSeparator()

        self.lockAction = action.getAction("looknfeel/lock_widget")
        self.contextMenu.addAction(self.lockAction)
        self.unlockAction = action.getAction("looknfeel/unlock_widget")
        self.contextMenu.addAction(self.unlockAction)
        self.recursivelyLockAction = action.getAction("looknfeel/recursively_lock_widget")
        self.contextMenu.addAction(self.recursivelyLockAction)
        self.recursivelyUnlockAction = action.getAction("looknfeel/recursively_unlock_widget")
        self.contextMenu.addAction(self.recursivelyUnlockAction)

        self.contextMenu.addSeparator()

        self.cutAction = action.getAction("all_editors/cut")
        self.contextMenu.addAction(self.cutAction)
        self.copyAction = action.getAction("all_editors/copy")
        self.contextMenu.addAction(self.copyAction)
        self.pasteAction = action.getAction("all_editors/paste")
        self.contextMenu.addAction(self.pasteAction)
        self.deleteAction = action.getAction("all_editors/delete")
        self.contextMenu.addAction(self.deleteAction)

        self.contextMenu.addSeparator()

        self.copyNamePathAction = action.getAction("looknfeel/copy_widget_path")
        self.contextMenu.addAction(self.copyNamePathAction)

    def contextMenuEvent(self, event):
        selectedIndices = self.selectedIndexes()

        # TODO: since these actions enabled state depends on the selection,
        # move the enabling/disabling to a central "selection changed" handler.
        # The handler should be called on tab activations too because
        # activating a tab changes the selection, effectively.
        # We don't touch the cut/copy/paste actions because they're shared
        # among all editors and disabling them here would disable them
        # for the other editors too.
        haveSel = len(selectedIndices) > 0
        self.copyNamePathAction.setEnabled(haveSel)
        self.renameAction.setEnabled(haveSel)

        self.lockAction.setEnabled(haveSel)
        self.unlockAction.setEnabled(haveSel)
        self.recursivelyLockAction.setEnabled(haveSel)
        self.recursivelyUnlockAction.setEnabled(haveSel)

        self.deleteAction.setEnabled(haveSel)

        self.contextMenu.exec_(event.globalPos())

    def editSelectedWidgetName(self):
        selectedIndices = self.selectedIndexes()
        if len(selectedIndices) == 0:
            return
        self.setCurrentIndex(selectedIndices[0])
        self.edit(selectedIndices[0])

    def copySelectedWidgetPaths(self):
        selectedIndices = self.selectedIndexes()
        if len(selectedIndices) == 0:
            return

        paths = []
        for index in selectedIndices:
            item = self.model().itemFromIndex(index)
            if item.manipulator is not None:
                paths.append(item.manipulator.widget.getNamePath())

        if len(paths) > 0:
            # sort (otherwise the order is the item selection order)
            paths.sort()
            QtGui.QApplication.clipboard().setText(os.linesep.join(paths))

    def setSelectedWidgetsLocked(self, locked, recursive = False):
        selectedIndices = self.selectedIndexes()
        if len(selectedIndices) == 0:
            return

        # It is possible that we will make superfluous lock actions if user
        # selects widgets in a hierarchy (parent & child) and then does
        # a recursive lock. This doesn't do anything harmful so we don't
        # have any logic to prevent that.

        paths = []
        for index in selectedIndices:
            item = self.model().itemFromIndex(index)
            if item.manipulator is not None:
                item.setLocked(locked, recursive)


class LookNFeelHierarchyDockWidget(QtGui.QDockWidget):
    """Displays and manages the widget hierarchy. Contains the LookNFeelHierarchyTreeWidget.
    """

    def __init__(self, visual):
        super(LookNFeelHierarchyDockWidget, self).__init__()

        self.visual = visual

        self.ui = ceed.ui.editors.looknfeel.looknfeelhierarchydockwidget.Ui_LookNFeelHierarchyDockWidget()
        self.ui.setupUi(self)

        self.ignoreSelectionChanges = False

        self.model = LookNFeelHierarchyTreeModel(self)
        self.treeView = self.findChild(LookNFeelHierarchyTreeView, "treeView")
        self.treeView.dockWidget = self
        self.treeView.setModel(self.model)

        self.rootWidgetManipulator = None

    def setRootWidgetManipulator(self, root):
        """Sets the widget manipulator that is at the root of our observed hierarchy.
        Uses getTreeItemForManipulator to recursively populate the tree.
        """

        self.rootWidgetManipulator = root
        self.model.setRootManipulator(root)
        self.treeView.expandToDepth(0)

    def refresh(self):
        """Refreshes the entire hierarchy completely from scratch"""

        self.setRootWidgetManipulator(self.rootWidgetManipulator)

    def keyReleaseEvent(self, event):
        if event.key() == QtCore.Qt.Key_Delete:
            handled = self.visual.scene.deleteSelectedWidgets()

            if handled:
                return True

        return super(LookNFeelHierarchyDockWidget, self).keyReleaseEvent(event)


class WidgetMultiPropertyWrapper(pt.properties.MultiPropertyWrapper):
    """Overrides the default MultiPropertyWrapper to update the 'inner properties'
    and then create undo commands to update the CEGUI widgets.
    """

    def __init__(self, templateProperty, innerProperties, takeOwnership, ceguiProperty=None, ceguiSets=None, visual=None):
        super(WidgetMultiPropertyWrapper, self).__init__(templateProperty, innerProperties, takeOwnership)

        self.ceguiProperty = ceguiProperty
        self.ceguiSets = ceguiSets
        self.visual = visual

    def tryUpdateInner(self, newValue, reason=pt.properties.Property.ChangeValueReason.Unknown):
        if super(WidgetMultiPropertyWrapper, self).tryUpdateInner(newValue, reason):
            ceguiValue = unicode(newValue)

            # create and execute command
            widgetPaths = []
            undoOldValues = {}

            # set the properties where applicable
            for ceguiSet in self.ceguiSets:
                widgetPath = ceguiSet.getNamePath()
                widgetPaths.append(widgetPath)
                undoOldValues[widgetPath] = self.ceguiProperty.get(ceguiSet)

            # create the undoable command
            # but tell it not to trigger the property changed callback
            # on first run because our on value has already changed,
            # we just want to sync the widget value now.
            cmd = undo.PropertyEditCommand(self.visual, self.ceguiProperty.getName(), widgetPaths, undoOldValues, ceguiValue,
                                           ignoreNextPropertyManagerCallback = True)
            self.visual.tabbedEditor.undoStack.push(cmd)

            # make sure to redraw the scene to preview the property
            self.visual.scene.update()

            return True

        return False

class EditingScene(cegui_widgethelpers.GraphicsScene):
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

    def getManipulatorByPath(self, widgetPath):
        path = widgetPath.split("/", 1)
        assert(len(path) >= 1)

        if len(path) == 1:
            assert(path[0] == self.rootManipulator.widget.getName())

            return self.rootManipulator

        else:
            # path[1] is the remainder of the path
            return self.rootManipulator.getManipulatorByPath(path[1])

    def setCEGUIDisplaySize(self, width, height, lazyUpdate = True):
        # overridden to keep the manipulators in sync

        super(EditingScene, self).setCEGUIDisplaySize(width, height, lazyUpdate)

        # FIXME: this won't do much with lazyUpdate = False
        if hasattr(self, "rootManipulator") and self.rootManipulator is not None:
            self.rootManipulator.updateFromWidget()

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

        if event.key() == QtCore.Qt.Key_Delete:
            handled = self.deleteSelectedWidgets()

        if not handled:
            super(EditingScene, self).keyReleaseEvent(event)

        else:
            event.accept()

    def dragEnterEvent(self, event):
        # if the root manipulator is in place the QGraphicsScene machinery will take care of drag n drop
        # the graphics items (manipulators in fact) have that implemented already
        if self.rootManipulator is not None:
            super(EditingScene, self).dragEnterEvent(event)

        else:
            # otherwise we should accept a new root widget to the empty Look n' Feel if it's a new widget
            if event.mimeData().hasFormat("application/x-ceed-widget-type"):
                event.acceptProposedAction()

    def dragMoveEvent(self, event):
        # if the root manipulator is in place the QGraphicsScene machinery will take care of drag n drop
        # the graphics items (manipulators in fact) have that implemented already
        if self.rootManipulator is not None:
            super(EditingScene, self).dragMoveEvent(event)

        else:
            # otherwise we should accept a new root widget to the empty Look n' Feel if it's a new widget
            if event.mimeData().hasFormat("application/x-ceed-widget-type"):
                event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        # if the root manipulator is in place the QGraphicsScene machinery will take care of drag n drop
        # the graphics items (manipulators in fact) have that implemented already
        if self.rootManipulator is not None:
            super(EditingScene, self).dragEnterEvent(event)

        else:
            pass

    def dropEvent(self, event):
        # if the root manipulator is in place the QGraphicsScene machinery will take care of drag n drop
        # the graphics items (manipulators in fact) have that implemented already
        if self.rootManipulator is not None:
            super(EditingScene, self).dropEvent(event)

        else:
            data = event.mimeData().data("application/x-ceed-widget-type")

            if data:
                widgetType = data.data()

                cmd = undo.CreateCommand(self.visual, "", widgetType, widgetType.rsplit("/", 1)[-1])
                self.visual.tabbedEditor.undoStack.push(cmd)

                event.acceptProposedAction()

            else:
                event.ignore()

# needs to be at the end to sort circular deps
import ceed.ui.editors.looknfeel.looknfeelhierarchydockwidget
import ceed.ui.editors.looknfeel.looknfeelwidgetlookselectorwidget
import ceed.ui.editors.looknfeel.looknfeelpropertyeditordockwidget

# needs to be at the end, import to get the singleton
from ceed import mainwindow
from ceed import settings
from ceed import action
