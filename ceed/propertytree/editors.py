"""The standard editors for the property tree.

PropertyEditorRegistry -- Maintains a list of the available editors and the types they can edit; creates the appropriate editor for a property.
PropertyEditor -- The base class for all property editors.
StringPropertyEditor -- Editor for strings.
NumericPropertyEditor -- Editor for integers and floating point numbers.
StringWrapperValidator -- Edit widget validator for the StringWrapperProperty.
"""

from . import utility

from .properties import Property

from PySide.QtGui import QLineEdit
from PySide.QtGui import QSpinBox
from PySide.QtGui import QValidator

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

    def __init__(self, boundProperty, instantApply=True):
        """Initialise an instance and keeps a reference
        to the property that will be edited.
        """
        self.editWidget = None
        self.property = boundProperty
        self.instantApply = self.property.getEditorOption("instantApply", instantApply)

        # see valueChanging()
        self.widgetValueInitialized = False

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
        """Read and return a tuple with the current value of the widget
        and a boolean specifying whether it's a valid value or not."""
        return None, False

    def setWidgetValueFromProperty(self):
        """Set the value of the widget to the value of the property.
        
        Implementors should set self.widgetValueInitialized to True
        *after* setting the widget value.
        """
        self.widgetValueInitialized = True

    def setPropertyValueFromWidget(self):
        """Set the value of the property to value of the widget."""
        value, valid = self.getWidgetValue()
        if valid and value != self.property.value:
            self.property.setValue(value, Property.ChangeValueReason.Editor)

    def valueChanging(self):
        """Callback-style method used when the 'instantApply' option
        is True to update the property's value without waiting for
        the editor to commit the edit.
        Should be called by implementors whenever the value of
        the widget changes, even if it hasn't been committed.
        """
        if not self.instantApply:
            return False

        # We ignore the first event because that one
        # occurs when we initialise the edit widget's value.
        if not self.widgetValueInitialized:
            return False

        self.setPropertyValueFromWidget()
        return True

class StringPropertyEditor(PropertyEditor):

    @classmethod
    def getSupportedValueTypes(cls):
        return { str:0, unicode:0 }

    def createEditWidget(self, parent):
        self.editWidget = QLineEdit(parent)
        self.editWidget.textEdited.connect(self.valueChanging)

        # setup options
        options = self.property.getEditorOption("string/")
        go = utility.getDictionaryTreePath

        self.editWidget.setMaxLength(go(options, "maxLength", self.editWidget.maxLength()))
        self.editWidget.setPlaceholderText(go(options, "placeholderText", self.editWidget.placeholderText()))
        self.editWidget.setInputMask(go(options, "inputMask", self.editWidget.inputMask()))
        self.editWidget.setValidator(go(options, "validator", self.editWidget.validator()))

        return self.editWidget

    def getWidgetValue(self):
        return (self.editWidget.text(), True) if self.editWidget.hasAcceptableInput() else ("", False)

    def setWidgetValueFromProperty(self):
        value, valid = self.getWidgetValue()
        if (not valid) or (self.property.value != value):
            self.editWidget.setText(self.property.value)

        super(StringPropertyEditor, self).setWidgetValueFromProperty()

PropertyEditorRegistry._standardEditors.add(StringPropertyEditor)

class NumericPropertyEditor(PropertyEditor):

    @classmethod
    def getSupportedValueTypes(cls):
        return { int:0, float:-5 }

    def createEditWidget(self, parent):
        self.editWidget = QSpinBox(parent)
        self.editWidget.valueChanged.connect(self.valueChanging)

        # setup options
        options = self.property.getEditorOption("numeric/")
        go = utility.getDictionaryTreePath

        self.editWidget.setRange(go(options, "min", self.editWidget.minimum()),
                                 go(options, "max", self.editWidget.maximum()));
        self.editWidget.setSingleStep(go(options, "step", self.editWidget.singleStep()))

        return self.editWidget

    def getWidgetValue(self):
        return self.editWidget.value(), True

    def setWidgetValueFromProperty(self):
        if self.property.value != self.getWidgetValue():
            self.editWidget.setValue(self.property.value)

        super(NumericPropertyEditor, self).setWidgetValueFromProperty()

PropertyEditorRegistry._standardEditors.add(NumericPropertyEditor)

class StringWrapperValidator(QValidator):
    """Validate the edit widget value when editing
    a StringWrapperProperty.
    
    Using this prevents closing the edit widget using
    "Enter" when the value is invalid and allows the
    user the correct their mistake without losing any
    editing they have done.
    """
    def __init__(self, swProperty, parent=None):
        super(StringWrapperValidator, self).__init__(parent)
        self.property = swProperty

    def validate(self, inputStr, pos):
        _, valid = self.property.parseStringValue(inputStr)
        return QValidator.Intermediate if not valid else QValidator.Acceptable
