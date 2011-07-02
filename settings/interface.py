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
        self.qsettings = settings

from PySide.QtCore import *
from PySide.QtGui import *
    
class QtSettingsInterface(SettingsInterface, QTabWidget):
    def __init__(self, settings):
        super(QtSettingsInterface, self).__init__(settings)
        
        self.setTabPosition(QTabWidget.West)
        
        self.createUI()
        
    def createUI(self):
        for category in self.qsettings.categories:
            self.addTab(self.createUIForCategory(category), category.label)
            
    def createUIForCategory(self, category):
        ret = QWidget()
        layout = QVBoxLayout()
        
        for section in category.sections:
            layout.addWidget(self.createUIForSection(section))
        
        ret.setLayout(layout)
        
        return ret
    
    def createUIForSection(self, section):
        ret = QWidget()
        layout = QFormLayout()
        
        for entry in section.entries:
            layout.addRow(entry.label, self.createUIForEntry(entry))
            
        ret.setLayout(layout)
        return ret
    
    def createUIForEntry(self, entry):
        if entry.typeHint == "string":
            ret = QLineEdit()
            ret.setText(entry.value)
            
            return ret
            
        elif entry.typeHint == "colour":
            ret = QLineEdit()
            ret.setText(str(entry.value))
            
            return ret
        