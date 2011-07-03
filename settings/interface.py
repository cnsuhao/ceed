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

class SettingsInterface(object):
    def __init__(self, settings):
        self.settings = settings

from PySide.QtCore import *
from PySide.QtGui import *

import qtwidgets

class QtSettingsInterface(SettingsInterface, QDialog):
    def __init__(self, settings):
        SettingsInterface.__init__(self, settings)
        QDialog.__init__(self)
        
        self.setWindowTitle(self.settings.label)

        self.createUI()
        
    def createUI(self):
        # sort everything so that it comes at the right spot when iterating
        self.settings.sort()
        
        # the basic UI
        self.layout = QVBoxLayout()
        
        self.label = QLabel(self.settings.help)
        self.label.setWordWrap(True)
        self.layout.addWidget(self.label)
        
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.West)
        self.layout.addWidget(self.tabs)
        
        self.setLayout(self.layout)
        
        # for each category, add a tab on the left
        for category in self.settings.categories:
            self.tabs.addTab(self.createUIForCategory(category), category.label)
            
        # apply, cancel, etc...
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Apply | QDialogButtonBox.Ok | QDialogButtonBox.Discard)
        self.layout.addWidget(self.buttonBox)
        
    def createUIForCategory(self, category):
        ret = QWidget()
        layout = QVBoxLayout()
        
        for section in category.sections:
            layout.addWidget(self.createUIForSection(section))
        
        ret.setLayout(layout)
        
        return ret
    
    def createUIForSection(self, section):
        ret = QGroupBox()
        ret.setTitle(section.label)
        
        layout = QVBoxLayout()
        
        entries = QWidget()
        entriesLayout = QFormLayout()
        
        for entry in section.entries:
            entriesLayout.addRow(entry.label, self.createUIForEntry(entry))
            
        entries.setLayout(entriesLayout)
        layout.addWidget(entries)
        ret.setLayout(layout)
        
        return ret
    
    def createUIForEntry(self, entry):
        if entry.typeHint == "string":
            ret = QLineEdit()
            ret.setText(entry.value)
            ret.setToolTip(entry.help)
            ret.textEdited.connect(lambda text: setattr(entry, "editedValue", text))
            
            return ret
            
        elif entry.typeHint == "colour":
            ret = qtwidgets.ColourButton()
            ret.colour = entry.value
            ret.setToolTip(entry.help)
            ret.colourChanged.connect(lambda colour: setattr(entry, "editedValue", colour))
            
            return ret
        
        elif entry.typeHint == "pen":
            ret = qtwidgets.PenButton()
            ret.pen = entry.value
            ret.setToolTip(entry.help)
            ret.penChanged.connect(lambda pen: setattr(entry, "editedValue", pen))
            
            return ret
        