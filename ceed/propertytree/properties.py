"""The basic properties.

PropertyCategory -- A category, groups properties together.
Property -- The base class for all properties, has name, value, etc.
StringWrapperProperty -- Special purpose property to edit the string representation of another property.
"""

from collections import OrderedDict

from . import utility

class PropertyCategory(object):
    """A category for properties.
    Categories have a name and hold a list of properties.
    """
    def __init__(self, name):
        """Initialise the instance with the specified name."""
        self.name = name
        self.properties = OrderedDict()

    @staticmethod
    def categorisePropertyList(propertyList, unknownCategoryName="Unknown"):
        """Given a list of properties, create categories and add the
        properties to them based on their 'category' field.
        
        The unknownCategoryName is used for a category that holds all
        properties that have no 'category' specified.
        """
        categories = {}
        for prop in propertyList:
            catName = prop.category if prop.category else unknownCategoryName
            if not catName in categories:
                categories[catName] = PropertyCategory(catName)
            category = categories[catName]
            category.properties[prop.name] = prop

        return categories

class Property(object):
    """A property which is the base for all properties.
    
    The most important fields of a property are 'name' and 'value'.
    A property instance should be able to return the type of its value
    and has a simple mechanism to notify others when its value changes.
    """

    class ChangeValueReason(object):
        Unknown = 0
        ComponentValueChanged = 1
        ParentValueChanged = 2
        Editor = 3

    class ComponentsUpdateType(object):
        AfterCreate = 0,
        BeforeDestroy = 1

    def __init__(self, name, value=None, defaultValue=None, category=None, helpText=None, readOnly=False, editorOptions=None):
        """Initialise an instance using the specified parameters.
        
        The 'category' field is usually a string that is used by
        'PropertyCategory.categorisePropertyList()' to place the
        property in a category.
        
        In the default implementation, the 'editorOptions' argument
        should be a dictionary of options that will be passed to the
        editor of the property's value. See getEditorOption().
        """

        # prevent values that are Property instances themselves;
        # these have to be added as components if needed.
        if isinstance(value, Property):
            raise TypeError("The 'value' argument of the '%s' Property can't be a Property. Did you mean to create a component?" % name)

        self.name = str(name) # make sure it's string
        self.value = value
        self.defaultValue = defaultValue
        self.category = category
        self.helpText = helpText
        self.readOnly = readOnly
        self.editorOptions = editorOptions

        # Lists of callables (aka events, signals).
        self.valueChanged = set()               # takes two arguments: sender, reason
        self.componentsUpdate = set()           # takes two arguments: sender, update type

        # Create components
        self.createComponents()

    def finalise(self):
        """Perform any cleanup necessary."""
        self.finaliseComponents()
        self.valueChanged.clear()

    def createComponents(self):
        """Create an OrderedDict with the component-properties that make up
        this property.
        
        The default implementation is incomplete,
        it simply subscribes to the components' valueChanged event
        to be able to update this property's own value when
        their value changes. It also calls raiseComponentsUpdate().
        
        Implementors should create the components, make sure they
        are accessible from getComponents() and then call this
        as super().
        """
        components = self.getComponents()
        if components:
            for comp in components.values():
                comp.valueChanged.add(self.componentValueChanged)
            self.raiseComponentsUpdate(self.ComponentsUpdateType.AfterCreate)

    def getComponents(self):
        """Return the OrderedDict of the components, or None."""
        return None

    def finaliseComponents(self):
        """Clean up components.
        
        The default implementation is usually enough, it will
        unsubscribe from the components' events, finalise them
        and clear the components field. It will also call
        raiseComponentsUpdate().
        """
        components = self.getComponents()
        if components:
            self.raiseComponentsUpdate(self.ComponentsUpdateType.BeforeDestroy)
            for comp in components.values():
                # TODO: uncomment below to be safe, it's commented to test execution order
                #if self.componentValueChanged in comp.valueChanged:
                comp.valueChanged.remove(self.componentValueChanged)
                comp.finalise()
            components.clear()

    def valueType(self):
        """Return the type of this property's value.
        The default implementation simply returns the Python type()
        of the current value.
        """
        return type(self.value)

    def hasDefaultValue(self):
        return self.value == self.defaultValue

    def valueToString(self):
        """Return a string representation of the current value.
        """
        if self.value is not None:
            if issubclass(type(self.value), Property):
                return self.value.valueToString()
            return str(self.value)
        return ""

    def isStringRepresentationEditable(self):
        """Return True if the property supports editing its string representation,
        in addition to editing its components."""
        return False

    def parseStringValue(self, strValue):
        """Parse the specified string value and return
        a tuple with the parsed value and a boolean
        specifying success or failure.
        """
        return None, False

    def setValue(self, value, reason=ChangeValueReason.Unknown):
        """Change the current value to the one specified
        and notify all subscribers of the change. Return True
        if the value was changed, otherwise False.
        
        If the property has components, this method is responsible
        for updating their values, if necessary. The default
        implementation does this by calling 'self.updateComponents()'.
        
        Note: The default implementation ignores the call if the
        value being set is the same as the current value.
        """

        #TODO: Remove print
        print "Setting value of property '%s' to '%s'%s, reason=%s" % (self.name, str(value), " (same)" if value is self.value else "", reason)
        if self.value is not value:
            self.value = value

            # Do not update components if our own value was changed
            # in response to a component's value having changed.
            if reason != self.ChangeValueReason.ComponentValueChanged:
                self.updateComponents(self.ChangeValueReason.ParentValueChanged)

            # This must be raised after updating the components because handlers
            # of the event will probably want to use the components.
            self.raiseValueChanged(reason)

            return True

        return False

    def updateComponents(self, reason=None):
        pass

    def raiseValueChanged(self, reason=None):
        """Notify all subscribers that the current value
        has been changed.
        You don't usually need to call this directly, it is
        called as part of 'setValue()'.
        """
        for subscriber in self.valueChanged:
            subscriber(self, reason)

    def raiseComponentsUpdate(self, updateType):
        """Notify all subscribers that the components
        are about to be destroyed or have been created.
        """
        for subscriber in self.componentsUpdate:
            subscriber(self, updateType)

    def componentValueChanged(self, component, reason):
        """Callback called when a component's value changes.
        
        This will generally call setValue() to update this instance's
        value in response to the component's value change. If this
        happens, the call to setValue() should use ChangeValueReason.ComponentValueChanged.
        
        See the DictionaryProperty for a different implementation.
        """
        pass

    def getEditorOption(self, path, defaultValue=None):
        """Get the value of the editor option at the specified path string.
        
        Return 'defaultValue' if the option/path can't be found.
        """

        return utility.getDictionaryTreePath(self.editorOptions, path, defaultValue)

class StringWrapperProperty(Property):
    """Special purpose property used to wrap the string value
    of another property so it can be edited.
    """
    def __init__(self, innerProperty, instantApply=False):
        super(StringWrapperProperty, self).__init__(innerProperty.name + "__wrapper__",
                                                    value = innerProperty.valueToString(),
                                                    editorOptions = {"instantApply":instantApply}
                                                    )
        self.innerProperty = innerProperty

    def finalise(self):
        super(StringWrapperProperty, self).finalise()

    def setValue(self, value, reason=Property.ChangeValueReason.Unknown):
        # if setting the value of the wrapper succeeded
        if super(StringWrapperProperty, self).setValue(value, reason):
            # if the inner property deems the value valid
            value, valid = self.innerProperty.parseStringValue(value)
            if valid:
                # set the value to the inner property and return True
                self.innerProperty.setValue(value, reason)
                return True

        return False
