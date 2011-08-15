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

# pwr; 8/15/11
# - Widget wrapper that provides access to both the `declaration.Entry` and
#   the `PySide.Qt.*` widget.
class InterfaceEntry(QHBoxLayout):
    def __init__(self, data, widget):
        super(InterfaceEntry, self).__init__()
        self.name_ = data.name
        self.data_ = data
        self.widget_ = widget
        return

    def resetToOldValue(self):
        # FIXME: This wants to be multiple classes, so we don't have to do
        # ad-hoc type checking.
        if self.data_.widgetHint == 'string':
            self.widget_.setText(self.data_.value)
        elif self.data_.widgetHint == 'int':
            self.widget_.setText(str(self.data_.value))
        elif self.data_.widgetHint == 'float':
            self.widget_.setText(str(self.data_.value))
        elif self.data_.widgetHint == 'checkbox':
            self.widget_.setChecked(self.data_.value)
        elif self.data_.widgetHint == 'colour':
            self.widget_.setColour(self.data_.value)
        elif self.data_.widgetHint == 'pen':
            self.widget_.setPen(self.data_.value)
        elif self.data_.widgetHint == 'keySequence':
            self.widget_.setKeySequence(self.data_.value)
        self.data_.hasChanges = False
        return

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

        # pwr; 8/15/11
        # - We can be notified via Qt when a new tab is selected; alas, we
        #   would like to know where we are coming from, though.
        # - This assumes the settings dialog always starts at 0; a fair
        #   assumption, I think.
        self.oldTab = 0

        # pwr; 8/15/11
        # - Put the tabs on top; more in line with the average user
        #   expectations.
        self.tabs = QTabWidget()
        self.tabs.setTabPosition(QTabWidget.North)
        self.layout.addWidget(self.tabs)

        self.setLayout(self.layout)

        # for each category, add a tab
        for category in self.settings.categories:
            self.tabs.addTab(self.createUIForCategory(category), category.label)

        # pwr; 8/15/11
        # - Connect the tab widget to notify us when the index changes.
        # - Also, this signal is generated when the first tab is added; point
        #   being, it should always be done after the tabs are populated to
        #   avoid possible spuriousness.
        self.tabs.currentChanged.connect(self.slot_tabClickedAsterik)
        #self.tabs.currentChanged.connect(self.slot_tabClickedDialog)

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

        elif entry.widgetHint == "float":
            widget = QLineEdit()
            widget.setText(str(entry.value))
            widget.setToolTip(entry.help)
            widget.textChanged.connect(lambda text: setattr(entry, "editedValue", float(text)))
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

        # pwr; 8/15/11
        # - Replace `QHBoxLayout` with `InterfaceEntry`.
        #ret = QHBoxLayout()
        ret = InterfaceEntry(entry, widget)
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
            print('reject')
            self.settings.discardChanges()
            self.reject()

        # pwr; 8/15/11
        # - Unstar the categories.
        # FIXME: We should not have to do all this kung-fu; maybe a list of
        # modified categories? Or, better yet, a container for categories.
        for tabIndex in range(self.tabs.count()):
            text = self.tabs.tabText(tabIndex)
            if text[0] == '*':
                self.tabs.setTabText(tabIndex, text[2:])

    # pwr; 8/15/11
    # - This is the asterik version.
    # - Invoked when a new tab/category is selected.
    # - First, dig out the data object of the category.
    # - As soon as changes are detected, star the category.
    # - When changes are applied or discarded, unstar the category.
    def slot_tabClickedAsterik(self, newTab):
        # FIXME: Assumes the list indexes match.
        category = self.settings.categories[self.oldTab]

        # Determine if any changes exist
        haveChanges = False
        try:
            for section in category.sections:
                for entry in section.entries:
                    if entry.hasChanges:
                        haveChanges = True
                        raise StopIteration
        except StopIteration:
            pass

        # If changes, star the category
        if haveChanges:
            self.tabs.setTabText(self.oldTab, ' '.join(['*', category.label]))

        self.oldTab = newTab
        return

    # pwr; 8/15/11
    # - This is the modal dialog version.
    # - Invoked when a new tab/category is selected.
    # - First, dig out the data object of the category.
    # - If changes are present, pop up a dialog box about it.
    # - If not, do nothing.
    def slot_tabClickedDialog(self, newTab):
        # FIXME: Assumes the list indexes match.
        category = self.settings.categories[self.oldTab]

        # Determine if any changes exist
        changedEntries = []
        for section in category.sections:
            for entry in section.entries:
                if entry.hasChanges:
                    changedEntries.append(entry)

        # If changes, query the user about what to do
        if changedEntries:

            # Get the corresponding widgets
            changedWidgets = []
            widgets = self.tabs.findChildren(InterfaceEntry)
            for entry in changedEntries:
                for widget in widgets:
                    if entry.name == widget.name_:
                        changedWidgets.append(widget)

            changes = QDialog(self)
            changes.setWindowTitle('Apply or discard changes')
            changes.yep = QPushButton('Apply')
            changes.nope = QPushButton('Discard')

            layout = QVBoxLayout()
            layout.addWidget(changes.yep)
            layout.addWidget(changes.nope)
            changes.setLayout(layout)
            changes.adjustSize() # FIXME: Doesn't work.

            changes.yep.setDefault(True)
            changes.yep.clicked.connect(changes.accept)
            changes.nope.clicked.connect(changes.reject)
            rv = changes.exec_()
            if rv == QDialog.Accepted:
                self.settings.applyChanges()
            elif rv == QDialog.Rejected:
                self.settings.discardChanges()
                for widget in changedWidgets:
                    # Reset the window widget to reflect the value; at this
                    # point, it still reflects the edited value.
                    widget.resetToOldValue()

        self.oldTab = newTab
        return
