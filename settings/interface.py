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
# - The following are lightweight widget wrappers for each entry type.
# - In the future, maybe an 'interface_types' module.
# - At the moment, we style sheet effects propagate from parent to child, so
#   we have to constantly reset the widgets style sheets; investigate turning
#   this off (read: application side effects).
class InterfaceEntry(QHBoxLayout):
    def __init__(self, entry, widget):
        super(InterfaceEntry, self).__init__()
        self.entry = entry
        self.widget_ = widget
        return

    def resetToOldValue(self):
        self.entry.hasChanges = False
        return

    def onChange(self):
        # FIXME: I am setting the Section, not the row in the section.
        #self.widget_.parent().setStyleSheet('font: bold italic')
        return

    def onNormal(self):
        # FIXME: I am setting the Section, not the row in the section.
        #self.widget_.parent().setStyleSheet('font: normal')
        return

class InterfaceEntryString(InterfaceEntry):
    def __init__(self, entry, widget):
        super(InterfaceEntryString, self).__init__(entry, widget)
        return

    def resetToOldValue(self):
        self.widget_.setText(str(self.entry.value))
        super(InterfaceEntryString, self).resetToOldValue()
        return

    def onChange(self, text):
        self.entry.editedValue = str(text)

        super(InterfaceEntryString, self).onChange()
        self.widget_.setStyleSheet('font: normal')
        return

class InterfaceEntryInt(InterfaceEntry):
    def __init__(self, entry, widget):
        super(InterfaceEntryInt, self).__init__(entry, widget)
        return

    def resetToOldValue(self):
        self.widget_.setText(str(self.entry.value))
        super(InterfaceEntryInt, self).resetToOldValue()
        return

    def onChange(self, text):
        try:
            self.entry.editedValue = int(text)
        except ValueError:
            # Invalid key (e.g. letters).
            # - Remove last character from the widget.
            # - This could be safer (e.g. some use of 'isdigit').
            self.widget_.setText(self.widget_.text()[:-1])
            return

        super(InterfaceEntryInt, self).onChange()
        self.widget_.setStyleSheet('font: normal')
        return

class InterfaceEntryFloat(InterfaceEntry):
    def __init__(self, entry, widget):
        super(InterfaceEntryFloat, self).__init__(entry, widget)
        return

    def resetToOldValue(self):
        self.widget_.setText(str(self.entry.value))
        super(InterfaceEntryFloat, self).resetToOldValue()
        return

    def onChange(self, text):
        try:
            self.entry.editedValue = float(text)
        except ValueError:
            # Invalid key (e.g. letters).
            # - Remove last character from the widget.
            # - This could be safer (e.g. some use of 'isdigit').
            self.widget_.setText(self.widget_.text()[:-1])
            return

        super(InterfaceEntryFloat, self).onChange()
        self.widget_.setStyleSheet('font: normal')
        return

class InterfaceEntryCheckbox(InterfaceEntry):
    def __init__(self, entry, widget):
        super(InterfaceEntryCheckbox, self).__init__(entry, widget)
        return

    def resetToOldValue(self):
        self.widget_.setChecked(self.entry.value)
        super(InterfaceEntryCheckbox, self).resetToOldValue()
        return

    def onChange(self, state):
        self.entry.editedValue = True if state else False

        super(InterfaceEntryCheckbox, self).onChange()
        self.widget_.setStyleSheet('font: normal')
        return

class InterfaceEntryColour(InterfaceEntry):
    def __init__(self, entry, widget):
        super(InterfaceEntryColour, self).__init__(entry, widget)
        return

    def resetToOldValue(self):
        self.widget_.setColour(self.entry.value)
        super(InterfaceEntryColour, self).resetToOldValue()
        return

    def onChange(self, colour):
        self.entry.editedValue = colour

        super(InterfaceEntryColour, self).onChange()
        self.widget_.setStyleSheet('font: normal')
        return

class InterfaceEntryPen(InterfaceEntry):
    def __init__(self, entry, widget):
        super(InterfaceEntryPen, self).__init__(entry, widget)
        return

    def resetToOldValue(self):
        self.widget_.setPen(self.entry.value)
        super(InterfaceEntryPen, self).resetToOldValue()
        return

    def onChange(self, pen):
        self.entry.editedValue = pen

        super(InterfaceEntryPen, self).onChange()
        self.widget_.setStyleSheet('font: normal')
        return

class InterfaceEntryKeySequence(InterfaceEntry):
    def __init__(self, entry, widget):
        super(InterfaceEntryKeySequence, self).__init__(entry, widget)
        return

    def resetToOldValue(self):
        self.widget_.setKeySequence(self.entry.value)
        super(InterfaceEntryKeySequence, self).resetToOldValue()
        return

    def onChange(self, keySequence):
        self.entry.editedValue = keySequence

        super(InterfaceEntryKeySequence, self).onChange()
        self.widget_.setStyleSheet('font: normal')
        return

# pwr; 8/16/11
# - Widget wrapper that provides access to a `declaration.Category` instance.
# - I would like to be more useful.
class InterfaceCategory(QScrollArea):
    def __init__(self, data):
        super(InterfaceCategory, self).__init__()
        self.data_ = data
        return

    def markAsChanged(self):
        self.data_.markAsChanged()
        return

    def markAsUnchanged(self):
        self.data_.markAsUnchaged()
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
        self.tabs.currentChanged.connect(self.slot_tabClicked)

        # apply, cancel, etc...
        self.buttonBox = QDialogButtonBox(QDialogButtonBox.Apply | QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.buttonBox.clicked.connect(self.slot_buttonBoxClicked)
        self.layout.addWidget(self.buttonBox)

    def createUIForCategory(self, category):
        # pwr; 8/16/11
        # - Replace `QScrollArea` with `InterfaceCategory`.
        ret = InterfaceCategory(category)

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

    # pwr; 8/16/11
    # - Incorporate the `InterfaceEntry[*]` objects.
    def createUIForEntry(self, entry):
        ret = None
        widget = None

        if entry.widgetHint == "string":
            widget = QLineEdit()
            ret = InterfaceEntryString(entry, widget)
            widget.setText(entry.value)
            widget.setToolTip(entry.help)
            widget.textEdited.connect(ret.onChange)

        elif entry.widgetHint == "int":
            widget = QLineEdit()
            ret = InterfaceEntryInt(entry, widget)
            widget.setText(str(entry.value))
            widget.setToolTip(entry.help)
            widget.textEdited.connect(ret.onChange)
            widget.slot_resetToDefault = lambda: widget.setText(str(entry.defaultValue))

        elif entry.widgetHint == "float":
            widget = QLineEdit()
            ret = InterfaceEntryFloat(entry, widget)
            widget.setText(str(entry.value))
            widget.setToolTip(entry.help)
            widget.textEdited.connect(ret.onChange)
            widget.slot_resetToDefault = lambda: widget.setText(str(entry.defaultValue))

        elif entry.widgetHint == "checkbox":
            widget = QCheckBox()
            ret = InterfaceEntryCheckbox(entry, widget)
            widget.setChecked(entry.value)
            widget.setToolTip(entry.help)
            widget.stateChanged.connect(ret.onChange)
            widget.slot_resetToDefault = lambda: widget.setChecked(entry.defaultValue)

        elif entry.widgetHint == "colour":
            widget = qtwidgets.ColourButton()
            ret = InterfaceEntryColour(entry, widget)
            widget.colour = entry.value
            widget.setToolTip(entry.help)
            widget.colourChanged.connect(ret.onChange)
            widget.slot_resetToDefault = lambda: setattr(widget, "colour", entry.defaultValue)

        elif entry.widgetHint == "pen":
            widget = qtwidgets.PenButton()
            ret = InterfaceEntryPen(entry, widget)
            widget.pen = entry.value
            widget.setToolTip(entry.help)
            widget.penChanged.connect(ret.onChange)
            widget.slot_resetToDefault = lambda: setattr(widget, "pen", entry.defaultValue)

        elif entry.widgetHint == "keySequence":
            widget = qtwidgets.KeySequenceButton()
            ret = InterfaceEntryKeySequence(entry, widget)
            widget.keySequence = entry.value
            widget.setToolTip(entry.help)
            widget.keySequenceChanged.connect(ret.onChange)
            widget.slot_resetToDefault = lambda: setattr(widget, "keySequence", entry.defaultValue)

        if widget is None:
            raise RuntimeError("I don't understand widget hint '%s'" % (entry.widgetHint))
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

            # pwr; 8/16/11
            # - Reset all widgets to old values.
            # - Hooray, base class.
            # - FIXME: I would very much like to only operate on modified
            #   entries.
            for widget in self.tabs.findChildren(InterfaceEntry):
                widget.resetToOldValue()

        # pwr; 8/15/11
        # - All categories are now unchanged.
        for tabIndex in range(self.tabs.count()):
            categoryWidget = self.tabs.widget(tabIndex)
            categoryWidget.data_.markAsUnchanged()
            self.tabs.setTabText(tabIndex, categoryWidget.data_.label)

        # pwr; 8/16/11
        for widget in self.tabs.findChildren(InterfaceEntry):
            widget.onNormal()

    # pwr; 8/15/11
    # - Invoked when a new tab/category is selected.
    # - As soon as changes are detected, mark the category as changed.
    # - Ideally, this sort of operation should not trigger ex post facto; that
    #   is to say, because each Entry is notified immediately upon it's change,
    #   that should trigger this kind of operation; as opposed to the deferred
    #   operation via Qt as it is now.
    def slot_tabClicked(self, newTab):
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

        # Mark category as changed
        if haveChanges:
            category.markAsChanged()
            self.tabs.setTabText(self.oldTab, category.label)

        self.oldTab = newTab
        return
