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
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Apply | QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.clicked.connect(self.slot_buttonBoxClicked)
        self.layout.addWidget(self.buttonBox)
        
    def createUIForCategory(self, category):
        ret = QScrollArea()
        outerLayout = QVBoxLayout()
        inner = QWidget()
        layout = QFormLayout()
        
        for section in category.sections:
            layout.addWidget(self.createUIForSection(section))
        
        inner.setLayout(layout)
        ret.setWidget(inner)
        outerLayout.addWidget(inner)
        ret.setLayout(outerLayout)
        
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
        
        # FIXME: The group box shrinks vertically for some reason
        ret.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        return ret
    
    def createUIForEntry(self, entry):
        widget = None
        
        if entry.widgetHint == "string":
            widget = QLineEdit()
            widget.setText(entry.value)
            widget.setToolTip(entry.help)
            widget.textEdited.connect(lambda text: setattr(entry, "editedValue", text))
        
        elif entry.widgetHint == "int":
            widget = QLineEdit()
            widget.setText(str(entry.value))
            widget.setToolTip(entry.help)
            widget.textChanged.connect(lambda text: setattr(entry, "editedValue", int(text)))
            widget.slot_resetToDefault = lambda: widget.setText(str(entry.defaultValue))
            
        elif entry.widgetHint == "checkbox":
            widget = QCheckBox()
            widget.setChecked(entry.value)
            widget.setToolTip(entry.help)
            widget.stateChanged.connect(lambda state: setattr(entry, "editedValue", True if state else False))
            widget.slot_resetToDefault = lambda: widget.setChecked(entry.defaultValue)
            
        elif entry.widgetHint == "colour":
            widget = qtwidgets.ColourButton()
            widget.colour = entry.value
            widget.setToolTip(entry.help)
            widget.colourChanged.connect(lambda colour: setattr(entry, "editedValue", colour))
            widget.slot_resetToDefault = lambda: setattr(widget, "colour", entry.defaultValue)
        
        elif entry.widgetHint == "pen":
            widget = qtwidgets.PenButton()
            widget.pen = entry.value
            widget.setToolTip(entry.help)
            widget.penChanged.connect(lambda pen: setattr(entry, "editedValue", pen))
            widget.slot_resetToDefault = lambda: setattr(widget, "pen", entry.defaultValue)
        
        elif entry.widgetHint == "keySequence":
            widget = qtwidgets.KeySequenceButton()
            widget.keySequence = entry.value
            widget.setToolTip(entry.help)
            widget.keySequenceChanged.connect(lambda keySequence: setattr(entry, "editedValue", keySequence))
            widget.slot_resetToDefault = lambda: setattr(widget, "keySequence", entry.defaultValue)

        if widget is None:
            raise RuntimeError("I don't understand widget hint '%s'" % (entry.widgetHint))

        ret = QHBoxLayout()
        ret.addWidget(widget)
        
        resetToDefault = QPushButton()
        resetToDefault.setIcon(QIcon("icons/settings/reset_entry_to_default.png"))
        resetToDefault.setToolTip("Reset this settings entry to the default value")
        ret.addWidget(resetToDefault)
        resetToDefault.clicked.connect(widget.slot_resetToDefault)
        
        return ret
        
    def slot_buttonBoxClicked(self, button):
        if self.buttonBox.buttonRole(button) == QDialogButtonBox.ApplyRole:
            self.settings.applyChanges()
            
        elif self.buttonBox.buttonRole(button) == QDialogButtonBox.AcceptRole:
            self.settings.applyChanges()
            self.accept()
            
        elif self.buttonBox.buttonRole(button) == QDialogButtonBox.RejectRole:
            self.settings.discardChanges()
            self.reject()
        