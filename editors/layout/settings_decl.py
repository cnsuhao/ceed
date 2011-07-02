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

from PySide.QtGui import QColor

def declare(settings):
    category = settings.addCategory(name = "layout", label = "Layout editing")
    
    visual = category.addSection(name = "visual", label = "Visual editing")
    
    visual.addEntry(name = "normal_outline_colour", label = "Normal outline colour",
                    defaultValue = QColor(255, 255, 255, 150), typeHint = "colour",
                    sortingWeight = 1)
    
    visual.addEntry(name = "hover_outline_colour", label = "Hover outline colour",
                    defaultValue = QColor(0, 255, 255, 255), typeHint = "colour",
                    sortingWeight = 2)
    
    visual.addEntry(name = "resizing_outline_colour", label = "Outline colour while resizing",
                    defaultValue = QColor(255, 0, 255, 255), typeHint = "colour",
                    sortingWeight = 3)
    
    visual.addEntry(name = "moving_outline_colour", label = "Outline colour while moving",
                    defaultValue = QColor(255, 0, 255, 255), typeHint = "colour",
                    sortingWeight = 3)
