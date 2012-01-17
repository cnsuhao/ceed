"""The basic properties.

PropertyCategory -- A category, groups properties together.
Property -- The base class for all properties, has name, value, etc.
StringWrapperProperty -- Special purpose property to edit the string representation of another property.
"""

import operator

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

    def sortProperties(self, reverse=False):
        self.properties = OrderedDict(sorted(self.properties.items(), key=lambda t: t[0], reverse=reverse))

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
        InnerValueChanged = 4
        WrapperValueChanged = 5

    class ComponentsUpdateType(object):
        AfterCreate = 0
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
            raise TypeError("The 'value' argument of the '%s' Property can't be a Property." % name)

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

    def tryParse(self, strValue):
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

        If the property is a wrapper property (a proxy to another
        property), this method tries to set the value of the
        inner property first and bails out if it can't. The default
        implementation does this by calling 'self.tryUpdateInner()'.
        
        Note: The default implementation ignores the call if the
        value being set is the same as the current value.
        """

        print "Setting value of property '%s' to '%s'%s, reason=%s" % (self.name, str(value), " (same)" if value is self.value else "", reason)
        if self.value is not value:

            # Do not update inner properties if our own value was changed
            # in response to an inner property's value having changed.
            if reason != self.ChangeValueReason.InnerValueChanged:
                if not self.tryUpdateInner(value, self.ChangeValueReason.WrapperValueChanged):
                    return False

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

    def updateComponents(self, reason=ChangeValueReason.Unknown):
        """Update this property's components (if any) to match this property's value."""
        pass

    def tryUpdateInner(self, newValue, reason=ChangeValueReason.Unknown):
        """Try to update the inner property (if any) to the new value.
        
        Return True on success, False on failure.
        """
        return True

    def raiseValueChanged(self, reason=ChangeValueReason.Unknown):
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
                                                    editorOptions = { "instantApply": instantApply }
                                                    )
        self.innerProperty = innerProperty
        self.innerProperty.valueChanged.add(self.innerValueChanged)

    def finalise(self):
        if self.innerValueChanged in self.innerProperty.valueChanged:
            self.innerProperty.valueChanged.remove(self.innerValueChanged)
        super(StringWrapperProperty, self).finalise()

    def innerValueChanged(self, innerProperty, reason):
        self.setValue(self.innerProperty.valueToString(), Property.ChangeValueReason.InnerValueChanged)

    def tryUpdateInner(self, newValue, reason=Property.ChangeValueReason.Unknown):
        value, valid = self.innerProperty.tryParse(newValue)
        if valid:
            # set the value to the inner property and return True
            self.innerProperty.setValue(value, reason)
            return True

        return False

class MultiPropertyWrapper(Property):
    """Special purpose property used to group many properties of the same type in one."""

    @classmethod
    def gatherValueData(cls, properties):
        """Go through the properties and return the unique values and default values found,
        ordered by use count.
        """
        values = dict()
        defaultValues = dict()

        for prop in properties:
            value = prop.value
            if value in values:
                values[value] += 1
            else:
                values[value] = 1

            defaultValue = prop.defaultValue
            if defaultValue in defaultValues:
                defaultValues[defaultValue] += 1
            else:
                defaultValues[defaultValue] = 1

        values = [value for value, _ in sorted(values.iteritems(), key = operator.itemgetter(1), reverse = True)]
        defaultValues = [value for value, _ in sorted(defaultValues.iteritems(), key = operator.itemgetter(1), reverse = True)]

        return values, defaultValues

    def __init__(self, templateProperty, innerProperties, takeOwnership):
        """Initialise the instance with the specified properties.
        
        templateProperty -- A newly created instance of a property of the same type
                            as the properties that are to be wrapped. This should be
                            already initialised with the proper name, category, settings,
                            etc. It will be used internally and it will be owned by
                            this wrapper.
        innerProperties -- The list of properties to wrap, must have at least one
                            property and all properties must have the same type
                            or an error is raised.
        takeOwnership -- Boolean flag indicating whether this wrapper should take
                            ownership of the inner properties, destroying them when
                            it is destroyed.
        """

        if len(innerProperties) == 0:
            raise ValueError("The 'innerProperties' argument has no elements; at least one is required.")

        # ensure all properties have the same valueType
        valueType = templateProperty.valueType()
        for prop in innerProperties:
            if prop.valueType() != valueType:
                raise ValueError("The valueType() of all the inner properties must be the same.")

        self.templateProperty = templateProperty
        self.innerProperties = innerProperties
        self.ownsInnerProperties = True
        self.allValues, self.allDefaultValues = self.gatherValueData(self.innerProperties)

        self.templateProperty.setValue(self.allValues[0])
        self.templateProperty.defaultValue = self.allDefaultValues[0]

        # initialise with the most used value and default value
        super(MultiPropertyWrapper, self).__init__(name = self.templateProperty.name,
                                                   category = self.templateProperty.category,
                                                   helpText = self.templateProperty.helpText,
                                                   value = self.templateProperty.value,
                                                   defaultValue = self.templateProperty.defaultValue,
                                                   readOnly = self.templateProperty.readOnly
                                                   )

        # subscribe to the valueChanged event of the inner properties
        # to update our value if the value of one of them changes.
        for prop in self.innerProperties:
            prop.valueChanged.add(self.innerValueChanged)
        # subscribe to the valueChanged event of the template property.
        self.templateProperty.valueChanged.add(self.templateValueChanged)

    def finalise(self):
        for prop in self.innerProperties:
            # unregister from any events
            if self.innerValueChanged in prop.valueChanged:
                prop.valueChanged.remove(self.innerValueChanged)
            # if we own it, finalise it
            if self.ownsInnerProperties:
                prop.finalise()
        self.innerProperties = None

        self.templateProperty.valueChanged.remove(self.templateValueChanged)
        self.templateProperty.finalise()
        self.templateProperty = None

        super(MultiPropertyWrapper, self).finalise()

    def createComponents(self):
        # We don't call super because we don't need to subscribe
        # to the templateProperty's components!
        self.raiseComponentsUpdate(self.ComponentsUpdateType.AfterCreate)

    def getComponents(self):
        return self.templateProperty.getComponents()

    def finaliseComponents(self):
        # We don't call super because we don't actually own any
        # components, they're owned by the templateProperty
        self.raiseComponentsUpdate(self.ComponentsUpdateType.BeforeDestroy)

    def valueType(self):
        return self.templateProperty.valueType()

    def hasDefaultValue(self):
        return self.templateProperty.hasDefaultValue()

    def isStringRepresentationEditable(self):
        return self.templateProperty.isStringRepresentationEditable()

    def tryParse(self, strValue):
        return self.templateProperty.tryParse(strValue)

    def updateComponents(self, reason=Property.ChangeValueReason.Unknown):
        #self.templateProperty.updateComponents(reason)
        self.templateProperty.setValue(self.value, reason)

    def valueToString(self):
        if len(self.allValues) == 1:
            return super(MultiPropertyWrapper, self).valueToString()
        return "<multiple values>"

    def templateValueChanged(self, sender, reason):
        # The template's value is changed when it's components change
        # or when we change it's value directly to match our own.
        if reason == Property.ChangeValueReason.ComponentValueChanged:
            self.setValue(self.templateProperty.value, reason)

    def tryUpdateInner(self, newValue, reason=Property.ChangeValueReason.Unknown):
        for prop in self.innerProperties:
            prop.setValue(newValue, reason)

        return True

    def innerValueChanged(self, innerProperty, reason):
        self.allValues, self.allDefaultValues = self.gatherValueData(self.innerProperties)

        self.setValue(self.allValues[0], Property.ChangeValueReason.InnerValueChanged)
