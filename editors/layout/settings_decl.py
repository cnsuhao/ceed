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

def declare(settings):
    category = settings.createCategory(name = "layout", label = "Layout editing")
    
    visual = category.createSection(name = "visual", label = "Visual editing")
    
    # FIXME: Only applies to newly switched to visual modes!
    visual.createEntry(name = "continuous_rendering", type = bool, label = "Continuous rendering",
                       help = "Check this if you are experiencing redraw issues (your skin contains an idle animation or such).\nOnly applies to newly switched to visual modes so switch to Code mode or back or restart the application for this to take effect.",
                       defaultValue = False, widgetHint = "checkbox",
                       sortingWeight = 0)
    
    visual.createEntry(name = "normal_outline", type = QPen, label = "Normal outline",
                       defaultValue = QPen(QColor(255, 255, 255, 150)), widgetHint = "pen",
                       sortingWeight = 1)
    
    visual.createEntry(name = "hover_outline", type = QPen, label = "Hover outline",
                       defaultValue = QPen(QColor(0, 255, 255, 255)), widgetHint = "pen",
                       sortingWeight = 2)
    
    visual.createEntry(name = "resizing_outline", type = QPen, label = "Outline while resizing",
                       defaultValue = QPen(QColor(255, 0, 255, 255)), widgetHint = "pen",
                       sortingWeight = 3)
    
    visual.createEntry(name = "moving_outline", type = QPen, label = "Outline while moving",
                       defaultValue = QPen(QColor(255, 0, 255, 255)), widgetHint = "pen",
                       sortingWeight = 3)
