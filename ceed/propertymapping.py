from .qtwidgets import LineEditWithClearButton

from propertytree import Property
from propertytree import PropertyCategory
from propertytree import PropertyTreeWidget

from PySide.QtGui import QWidget
from PySide.QtGui import QVBoxLayout

class PropertyInspectorWidget(QWidget):

    def __init__(self, parent=None):
        super(PropertyInspectorWidget, self).__init__(parent)

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        self.filterBox = LineEditWithClearButton()
        self.filterBox.setPlaceholderText("Filter")
        self.ptree = PropertyTreeWidget()

        layout.addWidget(self.filterBox)
        layout.addWidget(self.ptree)

    def setPropertySets(self, ceguiPropertySets):
        man = CEGUIPropertyManager()
        props = man.buildProperties(ceguiPropertySets)
        categories = PropertyCategory.categorisePropertyList(props)
        self.ptree.load(categories)

class PropertyMappingEntry(object):
    pass

class PropertyMap(object):
    pass

class CEGUIPropertyManager(object):

    # Maps CEGUI data types (in string form) to Python types
    # TODO: This type mapping may not be necessary if we create our
    # own custom PropertyEditor(s) that use these string types directly.
    
    # CEGUI properties are accessed via string values.
    # We can either convert them to our own types here and have the editors
    # use those types, or have them as strings and make the editors
    # parse and write the strings as CEGUI expects them.
    # I think it's the same amount of work - I'd rather create the
    # types here in Python and those would parse and write the strings.
    
    _typeMap = {
                "something": int,
                "supertype": float
                }

    @staticmethod
    def getTypeFromCEGUITypeString(ceguiStrType):
        return CEGUIPropertyManager._typeMap.get(ceguiStrType, unicode)

    @staticmethod
    def getCEGUIPropertyGUID(ceguiProperty):
        # HACK: The GUID is used as a hash value and to be able
        # to tell if two properties are the same.
        # There's currently no way to get this information, apart
        # from examining the name, datatype, origin etc. of the property
        # and build a string/hash value out of it.
        # However, since CEGUI properties are defined as static,
        # we can cheat and use their memory address to compare them.
        return ceguiProperty

    # TODO: Remove this and create a Property subclass that
    # sets the value on the ceguiSets. Can it also listen for
    # value changes to the underlying ceguiSets' properties?
    def createProperty(self, ceguiProperty, ceguiSets):

        if len(ceguiSets) != 1:
            raise NotImplementedError("Only supports one selected widget at the moment. Sorry!")
        ceguiSet = ceguiSets[0]

        prop = Property(name = ceguiProperty.getName(),
                        category = ceguiProperty.getOrigin(),
                        helpText = ceguiProperty.getHelp(),
                        value = ceguiProperty.get(ceguiSet),
                        defaultValue = ceguiProperty.getDefault(ceguiSet),
                        readOnly = not ceguiProperty.isWritable())

        return prop

    # TODO: L-O-L it works! (so far)
    # TODO: Add a way to only show modified (non-default) or recently
    # used properties (filterbox? toggle/radio button? extra categories?)
    # TODO: Sort the categories and the properties inside categories
    # TODO: Make first column wider (the automatic way doesn't do what I want)

    def buildProperties(self, ceguiPropertySets):
        # short name
        cgSets = ceguiPropertySets

        if len(cgSets) == 0:
            return []

        # * A CEGUI property does not have a value, it's similar to a definition
        #   and we need an object that has that property to be able to get a value.
        # * Each CEGUI PropertySet (widget, font, others) has it's own list of properties.
        # * Some properties may be shared across PropertSets but some are not.
        #
        # It's pretty simple to map the properties 1:1 when we have only one
        # set to process. When we have more, however, we need to group the
        # properties that are shared across sets so we display them as one
        # property that affects all the sets that have it.
        # We use getCEGUIPropertyGUID() to determine if two CEGUI properties
        # are the same. 

        cgProps = dict()

        for cgSet in cgSets:
            propIt = cgSet.getPropertyIterator()

            while not propIt.isAtEnd():
                cgProp = propIt.getCurrentValue()
                guid = self.getCEGUIPropertyGUID(cgProp)

                # if we already know this property, add the current set
                # to the list.
                if guid in cgProps:
                    cgProps[guid][1].append(cgSet)
                # if it's a new property, check if it can be added
                else:
                    # we don't support unreadable properties
                    # TODO: check if hidden by the current mapping
                    if cgProp.isReadable():
                        cgProps[guid] = (cgProp, [cgSet])

                propIt.next()

        # Convert the CEGUI properties with their sets to propertytree properties.
        ptProps = [self.createProperty(cgProp, sets) for cgProp, sets in cgProps.values()]

        return ptProps
