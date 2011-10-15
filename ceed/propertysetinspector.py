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

import propertyinspector

import ui.propertysetinspector

# Unix like wildcard matching for property filtering
import fnmatch

# TODO: I am not entirely happy with this module and will likely rewrite it a bit

# !!!
# All this code assumes that Widget creators aren't stupid and won't try to
# add 2 different properties with same name and origin to 2 different widgets
#
# Name clashes with different origins should be fine
#
# TODO: I never do any testing for this!
# !!!

class PropertyValue(QStandardItem):
    """Standard item displaying and holding the value.
    This is displayed next to a PropertyEntry
    """
    
    def __init__(self, propertyEntry):
        super(PropertyValue, self).__init__()
        
        self.propertyEntry = propertyEntry
        self.setEditable(True)
        
        self.update()
            
    def update(self):
        self.setText(self.propertyEntry.getCurrentValue())
        palette = QApplication.palette()
        
        if self.propertyEntry.isCurrentValueDefault():
            font = QFont()
            font.setItalic(True)
            
            self.setFont(font)
            
            self.setForeground(QBrush(palette.color(QPalette.Disabled, QPalette.Text)))
            self.setBackground(QBrush(palette.color(QPalette.Disabled, QPalette.Base)))
            
        else:
            font = QFont()
            font.setPixelSize(14)
            
            self.setFont(font)
        
            self.setForeground(QBrush(palette.color(QPalette.Active, QPalette.Text)))
            self.setBackground(QBrush(palette.color(QPalette.Active, QPalette.Base)))
        
class PropertyEntry(QStandardItem):
    """Standard item displaying the name of a property
    """
        
    def __init__(self, category, propertyName):
        """category is the parent property category,
        propertyName is the property name of this entry
        """
        
        super(PropertyEntry, self).__init__()
        
        self.category = category
        self.propertyName = propertyName
        self.setText(propertyName)
        self.setEditable(False)
        
        font = QFont()
        font.setPixelSize(14)
        self.setFont(font)
        
        self.value = PropertyValue(self)
        
    def getPropertySets(self):
        return self.category.getPropertySets()
    
    def getCurrentValue(self):
        value = None
        missingInSome = False
        
        for set in self.getPropertySets():
            if not set.isPropertyPresent(self.propertyName):
                missingInSome = True
                continue
            
            if value is None:
                value = set.getProperty(self.propertyName)
                continue

            newValue = set.getProperty(self.propertyName)
            
            if value != newValue:
                return "<varies>"
        
        return value
    
    def getCurrentValues(self):
        ret = {}
        missingInSome = False
        
        for set in self.getPropertySets():
            if not set.isPropertyPresent(self.propertyName):
                missingInSome = True
                continue
            
            ret[set] = set.getProperty(self.propertyName)
                    
        return ret
    
    def isCurrentValueDefault(self):
        for set in self.getPropertySets():
            if set.isPropertyPresent(self.propertyName):
                if not set.isPropertyDefault(self.propertyName):
                    return False
        
        return True

    def getPropertyInstance(self):
        ret = None
        for set in self.getPropertySets():
            if set.isPropertyPresent(self.propertyName):
                if ret is None:
                    ret = set.getPropertyInstance(self.propertyName)
                    continue
                
                other = set.getPropertyInstance(self.propertyName)
                
                # Sanity checks, if these fail, there is a property name clash!
                assert(ret.getOrigin() == other.getOrigin())
                assert(ret.getHelp() == other.getHelp())
                assert(ret.getDataType() == other.getDataType())
        
        return ret

    def update(self):
        self.value.update()
    
class PropertyCategory(QStandardItem):
    """Groups properties of the same origin
    """ 
    
    def __init__(self, inspector, origin):
        """inspector is the parent property inspector (property categories shouldn't be nested),
        origin is the origin that all the properties in this category have
        """
        
        super(PropertyCategory, self).__init__()
        
        self.inspector = inspector
        
        label = origin
        # we strip the CEGUI/ if any because most users only use CEGUI stock widgets and it
        # would be superfluous for them to display CEGUI/ everywhere
        if label.startswith("CEGUI/"):
            label = label[6:]    
        self.setText(label)
        
        self.setEditable(False)
        
        palette = QApplication.palette()
        
        # we have to set both foreground and background role to prevent issues with various colour
        # settings on the systems (dark desktop skins vs light desktop skins...)
        self.setForeground(QBrush(palette.color(QPalette.Normal, QPalette.HighlightedText)))
        self.setBackground(QBrush(palette.color(QPalette.Normal, QPalette.Highlight)))
        
        font = QFont()
        font.setBold(True)
        font.setPixelSize(16)
        self.setData(font, Qt.FontRole)
        
        self.propertyCount = QStandardItem()
        
        # see the comment above about foreground and background :-)
        self.propertyCount.setData(QBrush(palette.color(QPalette.HighlightedText)), Qt.ForegroundRole)
        self.propertyCount.setData(QBrush(palette.color(QPalette.Highlight)), Qt.BackgroundRole)
        
        self.propertyCount.setEditable(False)
        
    def getPropertySets(self):
        return self.inspector.getPropertySets()
        
    def setFilterMatched(self, matched):
        palette = QApplication.palette()
        
        if matched:
            self.setData(QBrush(palette.color(QPalette.Normal, QPalette.HighlightedText)), Qt.ForegroundRole)
            self.setData(QBrush(palette.color(QPalette.Normal, QPalette.Highlight)), Qt.BackgroundRole)
        else:
            self.setData(QBrush(palette.color(QPalette.Disabled, QPalette.HighlightedText)), Qt.ForegroundRole)
            self.setData(QBrush(palette.color(QPalette.Disabled, QPalette.Highlight)), Qt.BackgroundRole)
        
    def filterProperties(self, filter):
        toShow = []
        toHide = []
        
        matches = 0
        
        i = 0
        while i < self.rowCount():
            propertyEntry = self.child(i, 0)
            
            match = fnmatch.fnmatch(propertyEntry.text(), filter)
            
            if match:
                matches += 1
                toShow.append(propertyEntry)
            else:
                toHide.append(propertyEntry)
            
            i += 1
 
        self.setFilterMatched(matches > 0)
        if filter != "*":
            self.propertyCount.setText("%i matches" % matches)
        else:
            self.propertyCount.setText("%i properties" % matches)
            
        return toShow, toHide

class PropertySetInspectorDelegate(QItemDelegate):
    """Qt model/view delegate that allows delegating editing and viewing to
    PropertyInspectors
    """
    
    def __init__(self, setInspector):
        super(PropertySetInspectorDelegate, self).__init__()
        
        self.setInspector = setInspector
    
    def createEditor(self, parent, option, index):
        propertyEntry = self.setInspector.getPropertyEntry(index)
        propertyInstance = propertyEntry.getPropertyInstance()
        inspector, mapping = self.setInspector.propertyInspectorManager.getInspectorAndMapping(propertyInstance.getOrigin(), propertyInstance.getName())
        
        if inspector is None:
            return None
        
        ret = inspector.createEditWidget(parent, propertyEntry, mapping)
    
        return ret
    
    def setEditorData(self, editorWidget, index):
        propertyEntry = self.setInspector.getPropertyEntry(index)
        if propertyEntry is None:
            return

        editorWidget.inspector.populateEditWidget(editorWidget, propertyEntry, editorWidget.mapping)
        
    def setModelData(self, editorWidget, model, index):
        propertyEntry = self.setInspector.getPropertyEntry(index)
        if propertyEntry is None:
            return
        
        editorWidget.inspector.notifyEditingEnded(editorWidget, propertyEntry, editorWidget.mapping)
        propertyEntry.update()

class PropertySetInspector(QWidget):
    """Allows browsing and editing of any CEGUI::PropertySet derived class"""
    
    propertyEditingStarted = Signal(str)
    propertyEditingProgress = Signal(str, str)
    propertyEditingEnded = Signal(str, dict, str)
    
    def __init__(self, parent = None):
        super(PropertySetInspector, self).__init__(parent)
        
        self.propertyInspectorManager = None
        
        self.ui = ui.propertysetinspector.Ui_PropertySetInspector()
        self.ui.setupUi(self)
        
        self.filterBox = self.findChild(QLineEdit, "filterBox")
        self.filterBox.textChanged.connect(self.filterChanged)
        
        self.view = self.findChild(QTreeView, "view")
        self.model = QStandardItemModel()
        
        self.setPropertySets([])
        
        self.view.setItemDelegate(PropertySetInspectorDelegate(self))
        self.view.setModel(self.model)

    def setPropertyInspectorManager(self, propertyInspectorManager):
        """You have to set a valid property inspector manager before doing any inspecting.
        
        This class handles editing of the individual properties
        """
        
        assert(self.propertySets == [])
        self.propertyInspectorManager = propertyInspectorManager

    def getPropertyEntry(self, index):
        if not index.parent().isValid():
            # definitely not a property entry if it doesn't have a parent
            return None
        
        category = self.model.item(index.parent().row(), 0)
        return category.child(index.row(), 0)
        
    def setPropertySets(self, sets):
        # prevent flicker
        self.setUpdatesEnabled(False)
        
        self.model.clear()
        self.model.setColumnCount(2)
        self.model.setHorizontalHeaderLabels(["Name", "Value"])
        self.propertySets = sets
        
        if len(self.propertySets) > 0:
            assert(self.propertyInspectorManager is not None)
            
            propertiesByOrigin = {}
            
            for set in self.propertySets:
                propertyIt = set.getPropertyIterator()
                
                while not propertyIt.isAtEnd():
                    property = propertyIt.getCurrentValue()
                    propertyName = property.getName()
                    origin = property.getOrigin()
                    
                    # skip over if this property is ignored
                    if not self.propertyInspectorManager.isPropertyIgnored(origin, propertyName):
                        if not propertiesByOrigin.has_key(origin):
                            propertiesByOrigin[origin] = []
                        
                        if propertyName not in propertiesByOrigin[origin]:
                            propertiesByOrigin[origin].append(propertyName)
                    
                    propertyIt.next()
                
            for origin, propertyNames in propertiesByOrigin.iteritems():
                category = PropertyCategory(self, origin)
                
                self.model.appendRow([category, category.propertyCount])
                
                propertyCount = 0
                for propertyName in propertyNames:
                    entry = PropertyEntry(category, propertyName)
                    category.appendRow([entry, entry.value])
                    propertyCount += 1
                    
                category.propertyCount.setText("%i properties" % propertyCount)
                    
            self.view.expandAll()
            self.setEnabled(True)
            
        else:
            self.setEnabled(False)
            
        self.setUpdatesEnabled(True)
        
    def getPropertySets(self):
        return self.propertySets
                
    def refresh(self, onlyValues = False):
        if onlyValues:
            for i in range(self.model.rowCount()):
                category = self.model.item(i)
                assert(isinstance(category, PropertyCategory))
                
                for j in range(category.rowCount()):
                    propertyEntry = category.child(j)
                    assert(isinstance(propertyEntry, PropertyEntry))
                    
                    propertyEntry.update()
                
        else:
            self.setPropertySets(self.propertySets)
    
    def filterChanged(self, filter):
        # we append star at the end by default (makes property filtering much more practical)
        filter = filter + "*"
        
        i = 0
        while i < self.model.rowCount():
            category = self.model.item(i, 0)
            toShow, toHide = category.filterProperties(filter)
            
            for entry in toShow:
                self.view.setRowHidden(entry.index().row(), entry.index().parent(), False)
                
            for entry in toHide:
                self.view.setRowHidden(entry.index().row(), entry.index().parent(), True)
            
            i += 1
