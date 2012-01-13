"""The standard composite properties.

DictionaryProperty -- Generic property based on a dictionary.
"""

from collections import OrderedDict

from . import Property

class DictionaryProperty(Property):
    """A generic composite property based on a dict (or OrderedDict).
    
    The key-value pairs are used as components. A value can be a Property
    itself, allowing nested properties and the creation of multi-level,
    hierarchical properties.
    
    Example::
        prop = DictionaryProperty(
                                "rectangle",
                                OrderedDict([
                                             ("X", 0),
                                             ("Y", 0),
                                             ("Width", 50),
                                             ("Height", 50),
                                             ("Colour", DictionaryProperty(
                                                                        "Colour",
                                                                        OrderedDict(
                                                                                [
                                                                                    ("Red", 255),
                                                                                    ("Green", 255),
                                                                                    ("Blue", 255)
                                                                                ])
                                                                        )
                                            )]),
                                readOnly=False)
    """

    def createComponents(self):
        self.components = OrderedDict()
        for name, value in self.value.items():
            # if the value of the item is a Property, make sure
            # it's in a compatible state (i.e. readOnly) and add it
            # as a component directly.
            if isinstance(value, Property):
                # make it read only if we're read only
                if self.readOnly:
                    value.readOnly = True
                # ensure it's name is the our key name
                value.name = str(name)
                # add it
                self.components[name] = value
            # if it's any other value, create a Property for it.
            else:
                self.components[name] = Property(name=name, value=value, defaultValue=value, readOnly=self.readOnly, editorOptions=self.editorOptions)

        # call super to have it subscribe to our components;
        # it will call 'getComponents()' to get them.
        super(DictionaryProperty, self).createComponents()

    def hasDefaultValue(self):
        # it doesn't really make sense to maintain a default value for this property.
        # we check whether our components have their default values instead.
        # FIXME: I think this might be a problem in cases where the components'
        # values haven't been updated yet but we check for the default value;
        # for example inside the callbacks of our valueChanged event.
        for comp in self.components.values():
            if not comp.hasDefaultValue():
                return False
        return True

    def getComponents(self):
        return self.components

    def valueToString(self):
        gen = ("{%s:%s}" % (prop.name, prop.valueToString()) for prop in self.components.values())
        return ",".join(gen)

    def componentValueChanged(self, component, reason):
        self.value[component.name] = component.value
        self.raiseValueChanged(Property.ChangeValueReason.ComponentValueChanged)

    def updateComponentValues(self, reason=Property.ChangeValueReason.Unknown):
        for name in self.value:
            self.components[name].setValue(self.value[name], reason)
