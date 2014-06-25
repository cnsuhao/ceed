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


class LookNFeelHierarchyItem(QtGui.QStandardItem):

    def __init__(self, lookNFeelNode):

        if lookNFeelNode is None:
            super(LookNFeelHierarchyItem, self).__init__("None")
            self.setToolTip("type: None")
        if isinstance(lookNFeelNode, PyCEGUI.WidgetLookFeel):
            super(LookNFeelHierarchyItem, self).__init__(lookNFeelNode.getName())
            self.setToolTip("type: WidgetLookFeel")

        # self.setData(manipulator.widget.getNamePath(), QtCore.Qt.UserRole)

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