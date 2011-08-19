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

# Notes
# - Changes propagate upwards from the InterfaceEntry types to the Categories;
#   in contrast, apply/discard propagate downwards from the Categories to the
#   InterfaceEntry types.
# - The reason this is so is because the individual widgets are used to drive
#   when something has changed; alternatively, the QTabWidget could be used,
#   but that puts a delay on recognizing when a changed has occured.

# Wrappers for each Entry type
# - Contain a `declaration.Entry` instance and a `QtGui` widget.
class InterfaceEntry(QHBoxLayout):
    def __init__(self, entry, parent):
        super(InterfaceEntry, self).__init__()
        self.entry = entry
        self.parent = parent
        return

    def _buildResetButton(self):
        ret = QPushButton()
        ret.setIcon(QIcon("icons/settings/reset_entry_to_default.png"))
        ret.setToolTip("Reset this settings entry to the default value")
        ret.clicked.connect(self.widget_.slot_resetToDefault)
        return ret

    def resetToOldValue(self):
        self.entry.hasChanges = False
        return

    def onChange(self):
        self.markAsChanged()
        self.parent.onChange(self)
        return

    def markAsChanged(self):
        self.entry.markAsChanged()
        return

    def markAsUnchanged(self):
        self.entry.markAsUnchanged()
        return

class InterfaceEntryString(InterfaceEntry):
    def __init__(self, entry, parent):
        super(InterfaceEntryString, self).__init__(entry, parent)
        self.widget_ = QLineEdit()
        self.widget_.setText(entry.value)
        self.widget_.setToolTip(entry.help)
        self.widget_.textEdited.connect(self.onChange)
        self.addWidget(self.widget_)
        self.addWidget(self._buildResetButton())
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
    def __init__(self, entry, parent):
        super(InterfaceEntryInt, self).__init__(entry, parent)
        self.widget_ = QLineEdit()
        self.widget_.setText(str(entry.value))
        self.widget_.setToolTip(entry.help)
        self.widget_.textEdited.connect(self.onChange)
        self.widget_.slot_resetToDefault = self.resetToDefaultValue
        self.addWidget(self.widget_)
        self.addWidget(self._buildResetButton())
        return

    def resetToOldValue(self):
        self.widget_.setText(str(self.entry.value))
        super(InterfaceEntryInt, self).resetToOldValue()
        return

    def resetToDefaultValue(self):
        if self.entry.editedValue != self.entry.defaultValue:
            self.onChange(self.entry.defaultValue)
            self.widget_.setText(str(self.entry.defaultValue))
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
    def __init__(self, entry, parent):
        super(InterfaceEntryFloat, self).__init__(entry, parent)
        self.widget_ = QLineEdit()
        self.widget_.setText(str(entry.value))
        self.widget_.setToolTip(entry.help)
        self.widget_.textEdited.connect(self.onChange)
        self.widget_.slot_resetToDefault = self.resetToDefaultValue
        self.addWidget(self.widget_)
        self.addWidget(self._buildResetButton())
        return

    def resetToOldValue(self):
        self.widget_.setText(str(self.entry.value))
        super(InterfaceEntryFloat, self).resetToOldValue()
        return

    def resetToDefaultValue(self):
        if self.entry.editedValue != self.entry.defaultValue:
            self.onChange(self.entry.defaultValue)
            self.widget_.setText(str(self.entry.defaultValue))
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
    def __init__(self, entry, parent):
        super(InterfaceEntryCheckbox, self).__init__(entry, parent)
        self.widget_ = QCheckBox()
        self.widget_.setChecked(entry.value)
        self.widget_.setToolTip(entry.help)
        self.widget_.stateChanged.connect(self.onChange)
        self.widget_.slot_resetToDefault = self.resetToDefaultValue
        self.addWidget(self.widget_)
        self.addWidget(self._buildResetButton())
        return

    def resetToOldValue(self):
        self.widget_.setChecked(self.entry.value)
        super(InterfaceEntryCheckbox, self).resetToOldValue()
        return

    def resetToDefaultValue(self):
        if self.entry.editedValue != self.entry.defaultValue:
            self.onChange(self.entry.defaultValue)
            self.widget_.setChecked(self.entry.defaultValue)
        return

    def onChange(self, state):
        self.entry.editedValue = True if state else False

        super(InterfaceEntryCheckbox, self).onChange()
        self.widget_.setStyleSheet('font: normal')
        return

class InterfaceEntryColour(InterfaceEntry):
    def __init__(self, entry, parent):
        super(InterfaceEntryColour, self).__init__(entry, parent)
        self.widget_ = qtwidgets.ColourButton()
        self.widget_.colour = entry.value
        self.widget_.setToolTip(entry.help)
        self.widget_.colourChanged.connect(self.onChange)
        self.widget_.slot_resetToDefault = self.resetToDefaultValue
        self.addWidget(self.widget_)
        self.addWidget(self._buildResetButton())
        return

    def resetToOldValue(self):
        self.widget_.setColour(self.entry.value)
        super(InterfaceEntryColour, self).resetToOldValue()
        return

    def resetToDefaultValue(self):
        if self.entry.editedValue != self.entry.defaultValue:
            self.onChange(self.entry.defaultValue)
            self.widget_.colour = self.entry.defaultValue
        return

    def onChange(self, colour):
        self.entry.editedValue = colour

        super(InterfaceEntryColour, self).onChange()
        self.widget_.setStyleSheet('font: normal')
        return

class InterfaceEntryPen(InterfaceEntry):
    def __init__(self, entry, parent):
        super(InterfaceEntryPen, self).__init__(entry, parent)
        self.widget_ = qtwidgets.PenButton()
        self.widget_.pen = entry.value
        self.widget_.setToolTip(entry.help)
        self.widget_.penChanged.connect(self.onChange)
        self.widget_.slot_resetToDefault = self.resetToDefaultValue
        self.addWidget(self.widget_)
        self.addWidget(self._buildResetButton())
        return

    def resetToOldValue(self):
        self.widget_.setPen(self.entry.value)
        super(InterfaceEntryPen, self).resetToOldValue()
        return

    def resetToDefaultValue(self):
        if self.entry.editedValue != self.entry.defaultValue:
            self.onChange(self.entry.defaultValue)
            self.widget_.pen = self.entry.defaultValue
        return

    def onChange(self, pen):
        self.entry.editedValue = pen

        super(InterfaceEntryPen, self).onChange()
        self.widget_.setStyleSheet('font: normal')
        return

class InterfaceEntryKeySequence(InterfaceEntry):
    def __init__(self, entry, parent):
        super(InterfaceEntryKeySequence, self).__init__(entry, parent)
        self.widget_ = qtwidgets.KeySequenceButton()
        self.widget_.keySequence = entry.value
        self.widget_.setToolTip(entry.help)
        self.widget_.keySequenceChanged.connect(self.onChange)
        self.widget_.slot_resetToDefault = self.resetToDefaultValue
        self.addWidget(self.widget_)
        self.addWidget(self._buildResetButton())
        return

    def resetToOldValue(self):
        self.widget_.setKeySequence(self.entry.value)
        super(InterfaceEntryKeySequence, self).resetToOldValue()
        return

    def resetToDefaultValue(self):
        if self.entry.editedValue != self.entry.defaultValue:
            self.onChange(self.entry.defaultValue)
            self.widget_.keySequence = self.entry.defaultValue
        return

    def onChange(self, keySequence):
        self.entry.editedValue = keySequence

        super(InterfaceEntryKeySequence, self).onChange()
        self.widget_.setStyleSheet('font: normal')
        return

# Factory: Return appropriate InterfaceEntry
# - Not exported; restricted to use within this module.
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

        for entry in section.entries:
            self.entriesLayout.addRow(entry.label, _InterfaceEntryFactory(entry, self))

        self.entries.setLayout(self.entriesLayout)
        self.layout.addWidget(self.entries)
        self.setLayout(self.layout)

        # FIXME: The group box shrinks vertically for some reason
        self.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        return

    def resetToOldValue(self):
        for entry in self.modifiedEntries:
            entry.resetToOldValue()
        return

    def onChange(self, entry):
        self.modifiedEntries.append(entry)
        self.markAsChanged()
        # FIXME: A pretty stinky indirect reference here.
        self.entriesLayout.labelForField(entry).setText(entry.entry.label)
        self.parent.onChange(self)
        return

    def markAsChanged(self):
        self.section.markAsChanged()
        return

    def markAsUnchanged(self):
        self.section.markAsUnchanged()
        for entry in self.modifiedEntries:
            entry.markAsUnchanged()
            # FIXME: A pretty stinky indirect reference here.
            self.entriesLayout.labelForField(entry).setText(entry.entry.label)
        self.modifiedEntries = []
        return

# Wrappers: Category
class InterfaceCategory(QScrollArea):
    def __init__(self, category, parent):
        super(InterfaceCategory, self).__init__()
        self.category = category
        self.parent = parent
        self.modifiedSections = []

        self.outerLayout = QVBoxLayout()
        self.inner = QWidget()
        self.layout = QFormLayout()

        for section in category.sections:
            self.layout.addWidget(InterfaceSection(section, self))

        self.inner.setLayout(self.layout)
        self.setWidget(self.inner)
        self.outerLayout.addWidget(self.inner)
        self.setLayout(self.outerLayout)

        # - The viewport is resizable (otherwise, it will scale the widget it
        #   is viewing).
        self.setWidgetResizable(True)
        return

    # - For scrollbars.
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Wheel:
            delta = event.delta()
            if delta < 0:
                self.verticalScrollBar().triggerAction(QAbstractSlider.SliderSingleStepAdd)
            else:
                self.verticalScrollBar().triggerAction(QAbstractSlider.SliderSingleStepSub)
            return True
        return QObject.eventFilter(self, obj, event)

    def resetToOldValue(self):
        for section in self.modifiedSections:
            section.resetToOldValue()
        return

    def onChange(self, section):
        self.modifiedSections.append(section)
        self.markAsChanged()
        return

    def markAsChanged(self):
        self.category.markAsChanged()
        self.parent.setTabText(self.parent.indexOf(self), self.category.label)
        return

    def markAsUnchanged(self):
        self.category.markAsUnchanged()
        self.parent.setTabText(self.parent.indexOf(self), self.category.label)
        for section in self.modifiedSections:
            section.markAsUnchanged()
        self.modifiedSections = []
        return
