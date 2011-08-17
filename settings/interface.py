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

# FIXME: Settings want to be uploaded (persist) as soon as they are applied;
# make it so.

# FIXME: Mouse wheel events inside the tab frames do not actually scroll; the
# mouse has to be over the scroll bar for it to receive the event.

class SettingsInterface(object):
    def __init__(self, settings):
        self.settings = settings

from PySide.QtCore import *
from PySide.QtGui import *

import qtwidgets

from interface_types import *

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
        self.tabs.setTabPosition(QTabWidget.North)
        self.layout.addWidget(self.tabs)

        self.setLayout(self.layout)

        # for each category, add a tab
        for category in self.settings.categories:
            self.tabs.addTab(InterfaceCategory(category, self.tabs), category.label)

        # apply, cancel, etc...
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Apply | QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.clicked.connect(self.slot_buttonBoxClicked)
        self.layout.addWidget(self.buttonBox)

    def slot_buttonBoxClicked(self, button):
        if self.buttonBox.buttonRole(button) == QDialogButtonBox.ApplyRole:
            self.settings.applyChanges()

        elif self.buttonBox.buttonRole(button) == QDialogButtonBox.AcceptRole:
            self.settings.applyChanges()
            self.accept()

        elif self.buttonBox.buttonRole(button) == QDialogButtonBox.RejectRole:
            self.settings.discardChanges()
            self.reject()

            # - Reset any entries with changes to their stored value.
            for tabIndex in range(self.tabs.count()):
                self.tabs.widget(tabIndex).resetToOldValue()

        # - Regardless of the action above, all categories are now unchanged.
        for tabIndex in range(self.tabs.count()):
            self.tabs.widget(tabIndex).markAsUnchanged()

        # FIXME: That is not entirely true; using the 'X' to close the Settings
        # dialog is not handled here; although, this "bug as a feature" allows
        # Settings to be modified, closed, and it will remember (but not apply)
        # the previous changes.
