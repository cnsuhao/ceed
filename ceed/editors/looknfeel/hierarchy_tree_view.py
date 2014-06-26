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

import PyCEGUI

import os

from ceed import action

from ceed.editors.looknfeel.hierarchy_tree_item import LookNFeelHierarchyItem

class LookNFeelHierarchyTreeView(QtGui.QTreeView):
    """The WidgetLookFeel hierarchy tree definition
    This is based on the QTreeWidget widget.
    """

    def __init__(self, parent=None):
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