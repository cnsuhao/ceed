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

import qtwidgets

# Implementation notes
# - The "change detection" scheme propagates upwards from the individual Entry
#   types to their parents (currently terminated at the Category/Tab level).
# - In contrast, when a user applies changes, this propagates downwards from
#   the Category/Tab level to the individual (modified) entries.
# - The reason is because the settings widgets (QLineEdit, QCheckBox, etc) are
#   used to notify the application when a change happens; and once changes are
#   applied, it is convenient to use an iterate/apply mechanism.

# Wrapper: Entry types
# - One for each 'widgetHint'.
class InterfaceEntry(QHBoxLayout):
    def __init__(self, entry, parent):
        super(InterfaceEntry, self).__init__()
        self.entry = entry
        self.parent = parent

    def _addBasicWidgets(self):
        self.addWidget(self.entryWidget)
        self.addWidget(self._buildResetButton())

    def _buildResetButton(self):
        self.entryWidget.slot_resetToDefault = self.resetToDefaultValue
        ret = QPushButton()
        ret.setIcon(QIcon("icons/settings/reset_entry_to_default.png"))
        ret.setToolTip("Reset this settings entry to the default value")
        ret.clicked.connect(self.entryWidget.slot_resetToDefault)
        return ret

    def discardChanges(self):
        self.entry.hasChanges = False

    def onChange(self):
        self.markAsChanged()
        self.parent.onChange(self)

    def markAsChanged(self):
        self.entry.markAsChanged()

    def markAsUnchanged(self):
        self.entry.markAsUnchanged()

class InterfaceEntryString(InterfaceEntry):
    def __init__(self, entry, parent):
        super(InterfaceEntryString, self).__init__(entry, parent)
        self.entryWidget = QLineEdit()
        self.entryWidget.setText(entry.value)
        self.entryWidget.setToolTip(entry.help)
        self.entryWidget.textEdited.connect(self.onChange)
        self._addBasicWidgets()

    def discardChanges(self):
        self.entryWidget.setText(str(self.entry.value))
        super(InterfaceEntryString, self).discardChanges()

    def onChange(self, text):
        self.entry.editedValue = str(text)
        super(InterfaceEntryString, self).onChange()

class InterfaceEntryInt(InterfaceEntry):
    def __init__(self, entry, parent):
        super(InterfaceEntryInt, self).__init__(entry, parent)
        self.entryWidget = QLineEdit()
        self.entryWidget.setText(str(entry.value))
        self.entryWidget.setToolTip(entry.help)
        self.entryWidget.textEdited.connect(self.onChange)
        self._addBasicWidgets()

    def discardChanges(self):
        self.entryWidget.setText(str(self.entry.value))
        super(InterfaceEntryInt, self).discardChanges()

    def resetToDefaultValue(self):
        defValue = self.entry.defaultValue
        if self.entry.editedValue != defValue:
            self.onChange(defValue)
            self.entryWidget.setText(str(defValue))

    def onChange(self, text):
        try:
            self.entry.editedValue = int(text)
        except ValueError:
            ew = self.entryWidget
            ew.setText(ew.text()[:-1])
            return
        super(InterfaceEntryInt, self).onChange()

class InterfaceEntryFloat(InterfaceEntry):
    def __init__(self, entry, parent):
        super(InterfaceEntryFloat, self).__init__(entry, parent)
        self.entryWidget = QLineEdit()
        self.entryWidget.setText(str(entry.value))
        self.entryWidget.setToolTip(entry.help)
        self.entryWidget.textEdited.connect(self.onChange)
        self._addBasicWidgets()

    def discardChanges(self):
        self.entryWidget.setText(str(self.entry.value))
        super(InterfaceEntryFloat, self).discardChanges()

    def resetToDefaultValue(self):
        defValue = self.entry.defaultValue
        if self.entry.editedValue != defValue:
            self.onChange(defValue)
            self.entryWidget.setText(str(defValue))

    def onChange(self, text):
        try:
            self.entry.editedValue = float(text)
        except ValueError:
            ew = self.entryWidget
            ew.setText(ew.text()[:-1])
        super(InterfaceEntryFloat, self).onChange()

class InterfaceEntryCheckbox(InterfaceEntry):
    def __init__(self, entry, parent):
        super(InterfaceEntryCheckbox, self).__init__(entry, parent)
        self.entryWidget = QCheckBox()
        self.entryWidget.setChecked(entry.value)
        self.entryWidget.setToolTip(entry.help)
        self.entryWidget.stateChanged.connect(self.onChange)
        self._addBasicWidgets()

    def discardChanges(self):
        self.entryWidget.setChecked(self.entry.value)
        super(InterfaceEntryCheckbox, self).discardChanges()

    def resetToDefaultValue(self):
        defValue = self.entry.defaultValue
        if self.entry.editedValue != defValue:
            self.onChange(defValue)
            self.entryWidget.setChecked(defValue)

    def onChange(self, state):
        self.entry.editedValue = state
        super(InterfaceEntryCheckbox, self).onChange()

class InterfaceEntryColour(InterfaceEntry):
    def __init__(self, entry, parent):
        super(InterfaceEntryColour, self).__init__(entry, parent)
        self.entryWidget = qtwidgets.ColourButton()
        self.entryWidget.colour = entry.value
        self.entryWidget.setToolTip(entry.help)
        self.entryWidget.colourChanged.connect(self.onChange)
        self._addBasicWidgets()

    def discardChanges(self):
        self.entryWidget.setColour(self.entry.value)
        super(InterfaceEntryColour, self).discardChanges()

    def resetToDefaultValue(self):
        defValue = self.entry.defaultValue
        if self.entry.editedValue != defValue:
            self.onChange(defValue)
            self.entryWidget.colour = defValue

    def onChange(self, colour):
        self.entry.editedValue = colour
        super(InterfaceEntryColour, self).onChange()

class InterfaceEntryPen(InterfaceEntry):
    def __init__(self, entry, parent):
        super(InterfaceEntryPen, self).__init__(entry, parent)
        self.entryWidget = qtwidgets.PenButton()
        self.entryWidget.pen = entry.value
        self.entryWidget.setToolTip(entry.help)
        self.entryWidget.penChanged.connect(self.onChange)
        self._addBasicWidgets()

    def discardChanges(self):
        self.entryWidget.setPen(self.entry.value)
        super(InterfaceEntryPen, self).discardChanges()

    def resetToDefaultValue(self):
        defValue = self.entry.defaultValue
        if self.entry.editedValue != defValue:
            self.onChange(defValue)
            self.entryWidget.pen = defValue

    def onChange(self, pen):
        self.entry.editedValue = pen
        super(InterfaceEntryPen, self).onChange()

class InterfaceEntryKeySequence(InterfaceEntry):
    def __init__(self, entry, parent):
        super(InterfaceEntryKeySequence, self).__init__(entry, parent)
        self.entryWidget = qtwidgets.KeySequenceButton()
        self.entryWidget.keySequence = entry.value
        self.entryWidget.setToolTip(entry.help)
        self.entryWidget.keySequenceChanged.connect(self.onChange)
        self._addBasicWidgets()

    def discardChanges(self):
        self.entryWidget.setKeySequence(self.entry.value)
        super(InterfaceEntryKeySequence, self).discardChanges()

    def resetToDefaultValue(self):
        defValue = self.entry.defaultValue
        if self.entry.editedValue != defValue:
            self.onChange(defValue)
            self.entryWidget.keySequence = defValue

    def onChange(self, keySequence):
        self.entry.editedValue = keySequence
        super(InterfaceEntryKeySequence, self).onChange()

# Factory: Return appropriate InterfaceEntry
# - Not exported; restricted to use within this module.
# - Could be replaced by a static mapping.
def _InterfaceEntryFactory(entry, parent):
    if entry.widgetHint == 'string':
        return InterfaceEntryString(entry, parent)
    elif entry.widgetHint == 'int':
        return InterfaceEntryInt(entry, parent)
    elif entry.widgetHint == 'float':
        return InterfaceEntryFloat(entry, parent)
    elif entry.widgetHint == 'checkbox':
        return InterfaceEntryCheckbox(entry, parent)
    elif entry.widgetHint == 'colour':
        return InterfaceEntryColour(entry, parent)
    elif entry.widgetHint == 'pen':
        return InterfaceEntryPen(entry, parent)
    elif entry.widgetHint == 'keySequence':
        return InterfaceEntryKeySequence(entry, parent)
    else:
        raise RuntimeError("I don't understand widget hint '%s'" % (entry.widgetHint))

# Wrapper: Section
class InterfaceSection(QGroupBox):
    def __init__(self, section, parent):
        super(InterfaceSection, self).__init__()
        self.section = section
        self.parent = parent
        self.modifiedEntries = []

        self.setTitle(section.label)

        self.layout = QVBoxLayout()

        self.entries = QWidget()
        self.entriesLayout = QFormLayout()

        addRow = self.entriesLayout.addRow
        [addRow(entry.label, _InterfaceEntryFactory(entry, self)) for entry in section.entries]

        self.entries.setLayout(self.entriesLayout)
        self.layout.addWidget(self.entries)
        self.setLayout(self.layout)

        # FIXME: The group box shrinks vertically for some reason
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)

    def discardChanges(self):
        [entry.discardChanges() for entry in self.modifiedEntries]

    def onChange(self, entry):
        self.modifiedEntries.append(entry)
        self.markAsChanged()
        # FIXME: This should be rolled into the InterfaceEntry types.
        self.entriesLayout.labelForField(entry).setText(entry.entry.label)
        self.parent.onChange(self)

    def markAsChanged(self):
        self.section.markAsChanged()

    def markAsUnchanged(self):
        self.section.markAsUnchanged()
        labelForField = self.entriesLayout.labelForField
        for entry in self.modifiedEntries:
            entry.markAsUnchanged()
            # FIXME: This should be rolled into the InterfaceEntry types.
            labelForField(entry).setText(entry.entry.label)
        self.modifiedEntries = []

# Wrapper: Category
class InterfaceCategory(QScrollArea):
    def __init__(self, category, parent):
        super(InterfaceCategory, self).__init__()
        self.category = category
        self.parent = parent
        self.modifiedSections = []

        self.outerLayout = QVBoxLayout()
        self.inner = QWidget()
        self.layout = QFormLayout()

        addWidget = self.layout.addWidget
        [addWidget(InterfaceSection(section, self)) for section in category.sections]

        self.inner.setLayout(self.layout)
        self.setWidget(self.inner)
        self.outerLayout.addWidget(self.inner)
        self.setLayout(self.outerLayout)

        self.setWidgetResizable(True)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Wheel:
            if event.delta() < 0:
                self.verticalScrollBar().triggerAction(QAbstractSlider.SliderSingleStepAdd)
            else:
                self.verticalScrollBar().triggerAction(QAbstractSlider.SliderSingleStepSub)
            return True
        return QObject.eventFilter(self, obj, event)

    def discardChanges(self):
        [section.discardChanges() for section in self.modifiedSections]

    def onChange(self, section):
        self.modifiedSections.append(section)
        self.markAsChanged()

    def markAsChanged(self):
        parent = self.parent
        self.category.markAsChanged()
        parent.setTabText(parent.indexOf(self), self.category.label)

    def markAsUnchanged(self):
        parent = self.parent
        self.category.markAsUnchanged()
        parent.setTabText(parent.indexOf(self), self.category.label)
        [section.markAsUnchanged() for section in self.modifiedSections]
        self.modifiedSections = []

# Wrapper: Tabs
# TODO
