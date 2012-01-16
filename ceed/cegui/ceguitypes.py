import re

class Base(object):

    @classmethod
    def parseStringValue(cls, strValue, target=None):
        return None, False

    @classmethod
    def fromString(cls, strValue):
        value, valid = cls.parseStringValue(strValue)
        if not valid:
            raise ValueError("String value '%s' can't be parsed." % strValue)
        return value

class UDim(Base):

    pattern = '\s*\{\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\}\s*'
    rex = re.compile(pattern)

    @classmethod
    def parseStringValue(cls, strValue, target=None):
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
        self.scale = scale
        self.offset = offset

    def __eq__(self, other):
        if isinstance(other, UDim):
            return self.scale == other.scale and self.offset == other.offset
        return False

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        return "{{ {}, {} }}".format(self.scale, self.offset)

    def parse(self, strValue):
        return UDim.parseStringValue(strValue, self)[1]


class USize(Base):

    pattern = '\s*\{' + \
              UDim.pattern + \
              ',' + \
              UDim.pattern + \
              '\}\s*'
    rex = re.compile(pattern)

    @classmethod
    def parseStringValue(cls, strValue, target=None):
        match = re.match(USize.rex, strValue)
        if match is None:
            return None, False

        width_scale = float(match.group(1))
        width_offset = float(match.group(2))
        height_scale = float(match.group(3))
        height_offset = float(match.group(4))

        if target is None:
            target = cls(UDim(width_scale, width_offset), UDim(height_scale, height_offset))
        else:
            target.width.scale = width_scale
            target.width.offset = width_offset
            target.height.scale = height_scale
            target.height.offset = height_offset

        return target, True

    def __init__(self, width=UDim(), height=UDim()):
        self.width = width
        self.height = height

    def __eq__(self, other):
        if isinstance(other, USize):
            return self.width == other.width and self.height == other.height
        return False

    def __ne__(self, other):
        return not (self == other)

    def __repr__(self):
        return "{{ {}, {} }}".format(self.width, self.height)

    def parse(self, strValue):
        return USize.parseStringValue(strValue, self)[1]
