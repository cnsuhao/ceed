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

    cat.createAction(name = "zoom_original", label = "Zoom original",
                     help = "Goes back to original 1:1 zoom.",
                     icon = QIcon("icons/layout_editing/zoom_original.png"))
    cat.createAction(name = "zoom_in", label = "Zoom in",
                     help = "Zooms the whole layout view closer (magnifying it by a factor of 2 from its current state).",
                     icon = QIcon("icons/layout_editing/zoom_in.png"))
    cat.createAction(name = "zoom_out", label = "Zoom out",
                     help = "Zooms the whole layout view further back (demagnifying it by a factor of 2 from its current state).",
                     icon = QIcon("icons/layout_editing/zoom_out.png"))
    
    cat.createAction(name = "align_hleft", label = "Align left (horizontally)",
                     help = "Sets horizontal alignment of all selected widgets to left.",
                     icon = QIcon("icons/layout_editing/align_hleft.png"))
    cat.createAction(name = "align_hcentre", label = "Align centre (horizontally)",
                     help = "Sets horizontal alignment of all selected widgets to centre.",
                     icon = QIcon("icons/layout_editing/align_hcentre.png"))
    cat.createAction(name = "align_hright", label = "Align right (horizontally)",
                     help = "Sets horizontal alignment of all selected widgets to right.",
                     icon = QIcon("icons/layout_editing/align_hright.png"))
    
    cat.createAction(name = "align_vtop", label = "Align top (vertically)",
                     help = "Sets vertical alignment of all selected widgets to top.",
                     icon = QIcon("icons/layout_editing/align_vtop.png"))
    cat.createAction(name = "align_vcentre", label = "Align centre (vertically)",
                     help = "Sets vertical alignment of all selected widgets to centre.",
                     icon = QIcon("icons/layout_editing/align_vcentre.png"))
    cat.createAction(name = "align_vbottom", label = "Align bottom (vertically)",
                     help = "Sets vertical alignment of all selected widgets to bottom.",
                     icon = QIcon("icons/layout_editing/align_vbottom.png"))
    
    cat.createAction(name = "delete", label = "Delete selected widgets",
                     help = "Deletes all selected widgets and their child widgets.",
                     icon = QIcon("icons/layout_editing/delete.png"),
                     defaultShortcut = QKeySequence(QKeySequence.Delete))
    
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
    
    cat.createAction(name = "focus_property_inspector_filter_box", label = "Focus property inspector filter box",
                     help = "This allows you to easily press a shortcut and immediately search through properties without having to reach for a mouse.",
                     icon = QIcon("icons/layout_editing/focus_property_inspector_filter_box.png"),
                     defaultShortcut = QKeySequence(QKeySequence.Find))
    
    cat.createAction(name = "copy_widget_path", label = "Copy widget paths",
                     help = "Copies the 'NamePath' properties of the selected widgets to the clipboard.",
                     icon = QIcon("icons/actions/copy.png"))
    
    cat.createAction(name = "rename", label = "Rename widget",
                     help = "Edits the selected widget's name.",
                     icon = QIcon("icons/layout_editing/rename.png"))
