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

from PySide.QtCore import *
from PySide.QtGui import *

def declare(actionManager):
    cat = actionManager.createCategory(name = "layout", label = "Layout Editor")
    
    cat.createAction(name = "snap_grid", label = "Snap widgets to parent's snap grid",
                     help = "When resizing and moving widgets, if checked this makes sure they snap to a snap grid (see settings for snap grid related entries), also shows the snap grid if checked.",
                     icon = QIcon("icons/layout_editing/snap_grid.png"),
                     defaultShortcut = QKeySequence(Qt.Key_Space)).setCheckable(True)
                     
    cat.createAction(name = "absolute_mode", label = "Resize and move widgets in absolute mode",
                     help = "When resizing and moving widgets, if checked this makes the delta absolute, it is relative if unchecked.",
                     icon = QIcon("icons/layout_editing/absolute_mode.png"),
                     defaultShortcut = QKeySequence(Qt.Key_A)).setCheckable(True)
                     
    cat.createAction(name = "normalise_position", label = "Normalise position (cycle)",
                     help = "If the position is mixed (absolute and relative) it becomes relative only, if it's relative it becomes absolute, if it's absolute it becomes relative.",
                     icon = QIcon("icons/layout_editing/normalise_position.png"),
                     defaultShortcut = QKeySequence(Qt.Key_D))
                     
    cat.createAction(name = "normalise_size", label = "Normalise size (cycle)",
                     help = "If the size is mixed (absolute and relative) it becomes relative only, if it's relative it becomes absolute, if it's absolute it becomes relative.",
                     icon = QIcon("icons/layout_editing/normalise_size.png"),
                     defaultShortcut = QKeySequence(Qt.Key_S))
