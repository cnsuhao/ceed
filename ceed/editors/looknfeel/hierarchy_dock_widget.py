##############################################################################
#   created:    25th June 2014
#   author:     Lukas E Meindl
##############################################################################
##############################################################################
#   CEED - Unified CEGUI asset editor
#
#   Copyright (C) 2011-2014   Martin Preisler <martin@preisler.me>
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

from PySide import QtCore
from PySide import QtGui

import ceed

import PyCEGUI

from ceed.editors.looknfeel.hierarchy_tree_model import LookNFeelHierarchyTreeModel
from ceed.editors.looknfeel.hierarchy_tree_view import LookNFeelHierarchyTreeView

class LookNFeelHierarchyDockWidget(QtGui.QDockWidget):
    """Displays and manages the widget hierarchy. Contains the LookNFeelHierarchyTreeWidget.
    """

    def __init__(self, visual, tabbedEditor):
        super(LookNFeelHierarchyDockWidget, self).__init__()

        self.visual = visual
        self.tabbedEditor = tabbedEditor

        self.ui = ceed.ui.editors.looknfeel.looknfeelhierarchydockwidget.Ui_LookNFeelHierarchyDockWidget()
        self.ui.setupUi(self)

        self.ignoreSelectionChanges = False

        self.model = LookNFeelHierarchyTreeModel(self)
        """ :type: LookNFeelHierarchyTreeModel"""

        self.widgetLookNameLabel = self.findChild(QtGui.QLabel, "widgetLookName")
        """ :type: QtGui.QLabel"""
        self.widgetLookNameLabel.setText("")

        self.displayStateCombobox = self.findChild(QtGui.QComboBox, "displayStateCombobox")
        """ :type: QtGui.QComboBox"""
        self.displayStateCombobox.currentIndexChanged.connect(self.slot_displayStateComboboxCurrentIndexChanged)

        self.treeView = self.findChild(LookNFeelHierarchyTreeView, "treeView")
        """ :type: LookNFeelHierarchyTreeView"""
        self.treeView.dockWidget = self
        self.treeView.setModel(self.model)

        self.updateToNewWidgetLook()

    def updateToNewWidgetLook(self):
        self.widgetLookNameLabel.setText(self.tabbedEditor.targetWidgetLook)
        self.updateStateCombobox()
        self.updateHierarchy()

    def updateStateCombobox(self):
        """
        We populate the combobox with a show-all option and display options for the different states
        in the WidgetLookFeel
        :return:
        """
        self.displayStateCombobox.blockSignals(True)
        self.displayStateCombobox.clear()

        widgetLookObject = None
        if self.tabbedEditor.targetWidgetLook == "":
            return
        else:
            widgetLookObject = PyCEGUI.WidgetLookManager.getSingleton().getWidgetLook(self.tabbedEditor.targetWidgetLook)

        self.displayStateCombobox.addItem("Show all", None)

        stateIter = widgetLookObject.getStateIterator()
        while not stateIter.isAtEnd():
            currentStateImagery = stateIter.getCurrentValue()
            self.displayStateCombobox.addItem(currentStateImagery.getName(), currentStateImagery.getName())
            stateIter.next()

        showAllIndex = self.displayStateCombobox.findData(None)
        self.displayStateCombobox.setCurrentIndex(showAllIndex)
        self.displayStateCombobox.blockSignals(False)

    def updateHierarchy(self):
        """
        Updates the hierarchy based on the WidgetLookFeel which was selected and optionally limiting
        the display to a specific StateImagery and its referenced elements and their children
        :return:
        """

        limitDisplayTo = self.displayStateCombobox.itemData(self.displayStateCombobox.currentIndex())

        widgetLook = self.tabbedEditor.targetWidgetLook
        if widgetLook != "":
            widgetLookObject = PyCEGUI.WidgetLookManager.getSingleton().getWidgetLook(widgetLook)
            self.model.updateTree(widgetLookObject, limitDisplayTo)
        else:
            self.model.updateTree(None, limitDisplayTo)

        self.treeView.expandAll()

    def slot_displayStateComboboxCurrentIndexChanged(self, index):
        self.updateHierarchy()

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

    def keyReleaseEvent(self, event):
        if event.key() == QtCore.Qt.Key_Delete:
            handled = self.visual.scene.deleteSelectedWidgets()

            if handled:
                return True

        return super(LookNFeelHierarchyDockWidget, self).keyReleaseEvent(event)