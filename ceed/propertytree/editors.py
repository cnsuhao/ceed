"""The standard editors for the property tree.

PropertyEditorRegistry -- Maintains a list of the available editors and the types they can edit; creates the appropriate editor for a property.
PropertyEditor -- The base class for all property editors.
NumericPropertyEditor -- Editors for integers and floating point numbers.
"""
from . import Property

from PySide.QtGui import QLineEdit
from PySide.QtGui import QSpinBox

class PropertyEditorRegistry(object):
    """The registry contains a (sorted) list of property editor
    types that can be used for each value type.
    """

    # Standard editors place themselves in this set,
    # used by registerStandardEditors().
    _standardEditors = set()

    def __init__(self, autoRegisterStandardEditors=False):
        """Initialise an empty instance by default.
        If "autoRegisterStandardsEditors" is True,
        automatically register the standard editors.
        """
        self.editorsForValueType = dict()
        self.registeredEditorTypes = set()
        if autoRegisterStandardEditors:
            self.registerStardardEditors()

    def register(self, editorType, priority=0):
        """Register an editor with the specified priority.
        Higher values equal higher priority.
        
        Note: The priority is added to the editor's preferred
        priority for each value type supported. For example. if
        an editor specifies priority 10 for integers, registering
        the editor with priority = -3 will register it for
        integers with priority 7.
        
        Note: Registering the same editor twice does nothing
        and does not change the priority.
        """
        # If the editor hasn't been registered here already
        if not editorType in self.registeredEditorTypes:
            self.registeredEditorTypes.add(editorType)
            # Get supported types and priorities
            for valueType, valuePriority in editorType.getSupportedValueTypes().items():
                tup = (priority + valuePriority, editorType)
                # If we don't know this value type at all,
                # create a new list for this value type having
                # only one element with this editor.
                if not valueType in self.editorsForValueType:
                    self.editorsForValueType[valueType] = [tup]
                # If we already know this value type,
                # append the new editor and sort again so make
                # those of higher priority be first.
                else:
                    self.editorsForValueType[valueType].append(tup)
                    self.editorsForValueType[valueType].sort(reverse = True)

    def registerStardardEditors(self):
        """Register the predefined editors to this instance."""
        for editor in self._standardEditors:
            self.register(editor)

    def createEditor(self, editProperty):
        """Create and return an editor for the specified property,
        or None if none can be found that have been registered and
        are capable of editing the property.
        
        If more than one editors that can edit the property have been
        registered, the one with the highest priority will be chosen.
        """
        valueType = editProperty.valueType()
        if valueType in self.editorsForValueType:
            return self.editorsForValueType[valueType][0][1](editProperty)

        # TODO: if property.isStringRepresentationEditable() find string editor and edit the string value
        return None

class PropertyEditor(object):
    """Base class for a property editor.
    
    A property editor instance is created when required
    to edit the value of a (supported) property.
    """

    @classmethod
    def getSupportedValueTypes(cls):
        """Return a dictionary containing the types supported by this
        editor and their priorities. The key is the type and the value
        is the priority.
        
        Example: ``{ int:0, float:-10 }``
            Uses the default priority for integers and is most likely
            the preferred editor unless another editor is registered
            with higher priority. Standard editors should always have
            the default (0) or less priority.
            It can also edit floats but it should have low priority
            for those types (maybe it truncates or rounds them).
        """
        return None

    def __init__(self, boundProperty):
        """Initialise an instance and keeps a reference
        to the property that will be edited.
        """
        self.editWidget = None
        self.property = boundProperty

    def createEditWidget(self, parent):
        """Create and return a widget that will be used
        to edit the property.
        
        This is a good place to set up minimums and maximums,
        allowed patterns, step sizes etc. but setting the value
        is not required because a call to setWidgetValue
        will follow.
        """
        return self.editWidget

    def getWidgetValue(self):
        """Read and return the current value of the widget."""
        return None

    def setWidgetValueFromProperty(self):
        """Set the value of the widget to the value of the property."""
        pass

    def setPropertyValueFromWidget(self):
        """Set the value of the property to value of the widget."""
        value = self.getWidgetValue()
        self.property.setValue(value, Property.ChangeValueReason.Editor)

class StringPropertyEditor(PropertyEditor):

    @classmethod
    def getSupportedValueTypes(cls):
        return { str:0 }

    # TODO: Live (immediate) edit
    def createEditWidget(self, parent):
        self.editWidget = QLineEdit(parent)
        return self.editWidget

    def getWidgetValue(self):
        return self.editWidget.text()

    def setWidgetValueFromProperty(self):
        self.editWidget.setText(self.property.value)

PropertyEditorRegistry._standardEditors.add(StringPropertyEditor)

class NumericPropertyEditor(PropertyEditor):

    @classmethod
    def getSupportedValueTypes(cls):
        return { int:0, float:0 }

    def createEditWidget(self, parent):
        self.editWidget = QSpinBox(parent)
        return self.editWidget

    def getWidgetValue(self):
        return self.editWidget.value()

    def setWidgetValueFromProperty(self):
        self.editWidget.setValue(self.property.value)

PropertyEditorRegistry._standardEditors.add(NumericPropertyEditor)
