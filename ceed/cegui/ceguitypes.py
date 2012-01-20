"""Lightweight CEGUI property value types that can parse and write text."""

import re

from abc import abstractmethod
from abc import ABCMeta

from collections import OrderedDict

from ..propertytree.properties import Property

class Base(object):
    """Abstract base class for all value types."""

    __metaclass__ = ABCMeta

    @classmethod
    def tryParse(cls, strValue, target=None):
        """Parse the specified string value and return
        a tuple with the parsed value and a boolean
        specifying success or failure.
        
        If 'target' is not None, update its attributes
        with the parse value.
        """
        pass

    @classmethod
    def fromString(cls, strValue):
        """Parse the specified string value and return
        a new instance of this type.
        Raise a ValueError if the string can't be parsed.
        """
        value, valid = cls.tryParse(strValue)
        if not valid:
            raise ValueError("Could not convert string to %s: '%s'." % (cls.__name__, strValue))
        return value

    @classmethod
    def getPropertyType(cls):
        pass

    def parse(self, strValue):
        return self.__class__.tryParse(strValue, self)[1]

    @abstractmethod
    def __hash__(self):
        pass

    @abstractmethod
    def __eq__(self, other):
        pass

    @abstractmethod
    def __repr__(self):
        pass

    def __ne__(self, other):
        """Default implementation of __ne__, negates __eq__!"""
        return not (self.__eq__(other))

class UDim(Base):
    """UDim"""

    pattern = '\s*\{\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\}\s*'
    rex = re.compile(pattern)

    @classmethod
    def tryParse(cls, strValue, target=None):
        match = re.match(UDim.rex, strValue)
        if match is None:
            return None, False

        scale = float(match.group(1))
        offset = float(match.group(2))

        if target is None:
            target = cls(scale, offset)
        else:
            target.scale = scale
            target.offset = offset

        return target, True

    def __init__(self, scale=0.0, offset=0.0):
        super(UDim, self).__init__()
        self.scale = float(scale)
        self.offset = float(offset)

    def __hash__(self):
        return hash((self.scale, self.offset))

    def __eq__(self, other):
        if isinstance(other, UDim):
            return self.scale == other.scale and self.offset == other.offset
        return False

    def __repr__(self):
        # use round because we want max x digits but not zero padded
        # and not in scientific notation
        #return "{{ {:f}, {:f} }}".format(self.scale, self.offset)
        return "{{ {}, {} }}".format(round(self.scale, 6), round(self.offset, 6))

    @classmethod
    def getPropertyType(cls):
        return UDimProperty

class USize(Base):
    """USize (uses UDim)"""

    pattern = '\s*\{' + \
              UDim.pattern + \
              ',' + \
              UDim.pattern + \
              '\}\s*'
    rex = re.compile(pattern)

    @classmethod
    def tryParse(cls, strValue, target=None):
        match = re.match(USize.rex, strValue)
        if match is None:
            return None, False

        widthScale = float(match.group(1))
        widthOffset = float(match.group(2))
        heightScale = float(match.group(3))
        heightOffset = float(match.group(4))

        if target is None:
            target = cls(UDim(widthScale, widthOffset), UDim(heightScale, heightOffset))
        else:
            target.width.scale = widthScale
            target.width.offset = widthOffset
            target.height.scale = heightScale
            target.height.offset = heightOffset

        return target, True

    def __init__(self, width=UDim(), height=UDim()):
        super(USize, self).__init__()
        self.width = width
        self.height = height

    def __hash__(self):
        return hash((hash(self.width), hash(self.height)))

    def __eq__(self, other):
        if isinstance(other, USize):
            return self.width == other.width and self.height == other.height
        return False

    def __repr__(self):
        return "{{ {}, {} }}".format(self.width, self.height)

    @classmethod
    def getPropertyType(cls):
        return USizeProperty


class BaseProperty(Property):
    """Base class for all Property types.
    
    Note that, by default, it expects the components to map
    directly to an attribute of it's value; with the first letter in lower case.
    
    For example the UDimProperty has two components, 'Scale' and 'Offset' and
    it also uses the UDim type that has the 'scale' and 'offset' attribute values.
    """

    def createComponents(self):
        super(BaseProperty, self).createComponents()

    def getComponents(self):
        return self.components

    @classmethod
    def getAttrName(cls, componentName):
        """Get the attribute name from the component name."""
        return componentName[:1].lower() + componentName[1:]

    def updateComponents(self, reason=Property.ChangeValueReason.Unknown):
        components = self.getComponents()
        if components is not None:
            for compName, compValue in components.items():
                # set component value from attribute value
                compValue.setValue(getattr(self.value, self.getAttrName(compName)), reason)

    def componentValueChanged(self, component, reason):
        # set attribute value from component value
        setattr(self.value, self.getAttrName(component.name), component.value)
        # trigger our value changed event directly because
        # we didn't call 'setValue()' to do it for us.
        self.valueChanged.trigger(self, Property.ChangeValueReason.ComponentValueChanged)

class UDimProperty(BaseProperty):
    """Property for UDim values."""

    def createComponents(self):
        self.components = OrderedDict()
        self.components["Scale"] = Property(name="Scale", value=self.value.scale, defaultValue=self.defaultValue.scale,
                                            readOnly=self.readOnly, editorOptions=self.editorOptions)
        self.components["Offset"] = Property(name="Offset", value=self.value.offset, defaultValue=self.defaultValue.offset,
                                            readOnly=self.readOnly, editorOptions=self.editorOptions)

        super(UDimProperty, self).createComponents()

    def isStringRepresentationEditable(self):
        return True

    def tryParse(self, strValue):
        return UDim.tryParse(strValue)

class USizeProperty(BaseProperty):
    """Property for USize values."""

    def createComponents(self):
        self.components = OrderedDict()
        self.components["Width"] = UDimProperty(name="Width", value=self.value.width, defaultValue=self.defaultValue.width,
                                                readOnly=self.readOnly, editorOptions=self.editorOptions)
        self.components["Height"] = UDimProperty(name="Height", value=self.value.height, defaultValue=self.defaultValue.height,
                                                readOnly=self.readOnly, editorOptions=self.editorOptions)

        super(USizeProperty, self).createComponents()

    def isStringRepresentationEditable(self):
        return True

    def tryParse(self, strValue):
        return USize.tryParse(strValue)
