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

from xml.etree import ElementTree

import math

class PropertyInspectorMapping(object):
    """Maps a CEGUI::Property (by origin and name) to a PropertyInspector to allow
    its viewing and editing"""
    
    def __init__(self, propertyOrigin = "", propertyName = "",
                       targetInspectorName = "", targetInspectorSettings = {}):
        self.propertyOrigin = propertyOrigin
        self.propertyName = propertyName
        self.targetInspectorName = targetInspectorName
        self.targetInspectorSettings = targetInspectorSettings
    
    def loadFromElement(self, element):
        self.propertyOrigin = element.get("propertyOrigin")
        self.propertyName = element.get("propertyName")
        self.targetInspectorName = element.get("targetInspectorName")
        self.targetInspectorSettings = {}
        
        for setting in element.findall("setting"):
            self.targetInspectorSettings[setting.get("name")] = setting.get("value")
    
    def saveToElement(self):
        element = ElementTree.Element("mapping")
        
        element.set("propertyOrigin", self.propertyOrigin)
        element.set("propertyName", self.propertyName)
        element.set("targetInspectorName", self.targetInspectorName)
        
        for name, value in self.targetInspectorSettings:
            setting = ElementTree.Element("setting")
            setting.set("name", name)
            setting.set("value", value)
            element.append(setting)
            
        return element

class PropertyInspector(object):
    """Interface class, derived classes implement the actual editing and viewing
    of properties
    """
    
    def canEdit(self, property):
        return False
    
    def getName(self):
        return None
    
    def createEditWidget(self, parent, propertyEntry, mapping):
        ret = self.impl_createEditWidget(parent, propertyEntry, mapping)
        ret.inspector = self
        ret.mapping = mapping
        ret.propertyEntry = propertyEntry
        
        propertySetInspector = propertyEntry.parent.parent
        propertySetInspector.propertyEditingStarted.emit(propertyEntry.property.getName())
        
        return ret 
    
    def impl_createEditWidget(self, parent, propertyEntry, mapping):
        pass
    
    def populateEditWidget(self, widget, propertyEntry, mapping):
        # save the old value
        widget.oldValue = propertyEntry.getCurrentValue()
        
        self.impl_populateEditWidget(widget, propertyEntry, mapping)
    
    def impl_populateEditWidget(self, widget, propertyEntry, mapping):
        pass
    
    def impl_populatePropertyEntry(self, widget, propertyEntry, mapping):
        # hopefully a reasonable default implementation
        propertyEntry.value.setText(self.getCurrentValueForProperty(widget, propertyEntry, mapping))
    
    def getCurrentValueForProperty(self, widget, propertyEntry, mapping):
        pass
    
    def notifyEditingProgress(self, widget, propertyEntry, mapping):
        propertySetInspector = propertyEntry.parent.parent
        value = self.getCurrentValueForProperty(widget, propertyEntry, mapping)
        
        propertySetInspector.propertyEditingProgress.emit(propertyEntry.property.getName(), value) 
    
    def notifyEditingEnded(self, widget, propertyEntry, mapping):
        propertySetInspector = propertyEntry.parent.parent
        oldValue = widget.oldValue
        value = self.getCurrentValueForProperty(widget, propertyEntry, mapping)
        
        self.impl_populatePropertyEntry(widget, propertyEntry, mapping)
        propertySetInspector.propertyEditingEnded.emit(propertyEntry.property.getName(), oldValue, value) 

class LineEditPropertyInspector(PropertyInspector):
    def canEdit(self):
        dataTypes = ["String"]
        return property.getDataType() in dataTypes
    
    def getName(self):
        return "LineEdit"
    
    def impl_createEditWidget(self, parent, propertyEntry, mapping):
        ret = QLineEdit(parent)
        ret.setAutoFillBackground(True)
        
        def slot_textChanged(newValue):
            self.notifyEditingProgress(ret, propertyEntry, mapping)
        
        ret.textChanged.connect(slot_textChanged)
        
        return ret
    
    def impl_populateEditWidget(self, widget, propertyEntry, mapping):
        value = propertyEntry.getCurrentValue()
        
        widget.setText(value)
        
    def getCurrentValueForProperty(self, widget, propertyEntry, mapping):
        return widget.text()
    
class TextEditPropertyInspector(PropertyInspector):
    def canEdit(self):
        dataTypes = ["String"]
        return property.getDataType() in dataTypes
    
    def getName(self):
        return "TextEdit"
    
    def impl_createEditWidget(self, parent, propertyEntry, mapping):
        ret = QTextEdit(parent)
        ret.setAutoFillBackground(True)
    
        def slot_textChanged():
            self.notifyEditingProgress(ret, propertyEntry, mapping)
        
        ret.textChanged.connect(slot_textChanged)
        
        return ret
    
    def impl_populateEditWidget(self, widget, propertyEntry, mapping):
        value = propertyEntry.getCurrentValue()
        
        widget.setText(value)
        
    def getCurrentValueForProperty(self, widget, propertyEntry, mapping):
        return widget.toPlainText()

class CheckBoxPropertyInspector(PropertyInspector):
    def canEdit(self, property):
        return property.getDataType() == "bool"
    
    def getName(self):
        return "CheckBox"
    
    def impl_createEditWidget(self, parent, propertyEntry, mapping):
        ret = QCheckBox(parent)
        ret.setAutoFillBackground(True)
        
        def slot_stateChanged(state):
            self.notifyEditingProgress(ret, propertyEntry, mapping)
        
        ret.stateChanged.connect(slot_stateChanged)
        
        return ret
    
    def impl_populateEditWidget(self, widget, propertyEntry, mapping):
        widget.setChecked(propertyEntry.getCurrentValue() == "True")
        
    def getCurrentValueForProperty(self, widget, propertyEntry, mapping):
        if widget.isChecked():
            return "True"
        else:
            return "False"

class SliderPropertyInspector(PropertyInspector):
    def canEdit(self):
        dataTypes = ["int", "float"]
        return property.getDataType() in dataTypes
    
    def getName(self):
        return "Slider"
    
    def impl_createEditWidget(self, parent, propertyEntry, mapping):
        slider = QSlider(parent)
        slider.setAutoFillBackground(True)
        slider.setOrientation(Qt.Horizontal)
        
        def slot_sliderValueChanged(newValue):
            self.notifyEditingProgress(slider, propertyEntry, mapping)
        
        slider.valueChanged.connect(slot_sliderValueChanged)

        return slider
    
    def impl_populateEditWidget(self, widget, propertyEntry, mapping):
        value = float(propertyEntry.getCurrentValue())
        denominator = float(mapping.targetInspectorSettings["denominator"])
        
        # multiply because we are converting from property value to slider position
        widget.setSliderPosition(math.trunc(value * denominator))
        
    def getCurrentValueForProperty(self, widget, propertyEntry, mapping):
        denominator = float(mapping.targetInspectorSettings["denominator"])
        ret = float(widget.sliderPosition()) / denominator
        
        return str(ret)
    
class PropertyInspectorManager(object):
    inspectors = [
        LineEditPropertyInspector(),
        TextEditPropertyInspector(),
        CheckBoxPropertyInspector(),
        SliderPropertyInspector()
    ]
    
    mappings = []
    
    @staticmethod
    def clearMappings():
        PropertyInspectorManager.mappings = []
    
    @staticmethod    
    def loadMappings(absolutePath):
        tree = ElementTree.parse(absolutePath)
        root = tree.getroot()
        
        assert(root.get("version") == "0.8")
        
        for mappingElement in root.findall("mapping"):
            mapping = PropertyInspectorMapping()
            mapping.loadFromElement(mappingElement)
            PropertyInspectorManager.mappings.append(mapping)
    
    @staticmethod
    def getInspectorAndMapping(property):
        # reversed because custom mappings loaded later override stock mappings loaded earlier
        for mapping in reversed(PropertyInspectorManager.mappings):
            if mapping.propertyOrigin == property.getOrigin() and mapping.propertyName == property.getName():
                for inspector in PropertyInspectorManager.inspectors:
                    if inspector.getName() == mapping.targetInspectorName:
                        return inspector, mapping
                
                raise Exception("Found a mapping but it's target is invalid, can't find any "
                                "inspector of name '%s'" % (mapping.targetInspectorName))
        
        # mapping doesn't exist        
        return None, None            