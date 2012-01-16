import operator

from collections import OrderedDict

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
        self.filterBox.textChanged.connect(self.filterChanged)

        self.ptree = PropertyTreeWidget()

        layout.addWidget(self.filterBox)
        layout.addWidget(self.ptree)

        self.propertyManager = None

    def setPropertyManager(self, propertyManager):
        self.propertyManager = propertyManager

    def setPropertySets(self, ceguiPropertySets):
        categories = self.propertyManager.buildCategories(ceguiPropertySets)

        # load them into the tree
        self.ptree.load(categories)

    # FIXME: Decide what to do here.
    def refresh(self, onlyValues = True):
        pass

    def filterChanged(self, filterText):
        self.ptree.setFilter(filterText)

class PropertyMappingEntry(object):
    pass

class PropertyMap(object):
    pass

class CEGUIPropertyWrapper(Property):

    @staticmethod
    def gatherData(ceguiProperty, ceguiSets):
        values = dict()
        defaultValues = dict()
        validSets = []
        propName = ceguiProperty.getName()
        for ceguiSet in ceguiSets:
            if ceguiSet.isPropertyPresent(propName):
                validSets.append(ceguiSet)

                value = ceguiProperty.get(ceguiSet)
                if value in values:
                    values[value] += 1
                else:
                    values[value] = 1

                defaultValue = ceguiProperty.getDefault(ceguiSet)
                if defaultValue in defaultValues:
                    defaultValues[defaultValue] += 1
                else:
                    defaultValues[defaultValue] = 1

        values = [value for value, _ in sorted(values.iteritems(), key = operator.itemgetter(1), reverse = True)]
        defaultValues = [value for value, _ in sorted(defaultValues.iteritems(), key = operator.itemgetter(1), reverse = True)]

        return validSets, values, defaultValues

    def __init__(self, ceguiProperty, ceguiSets):

        if len(ceguiSets) == 0:
            raise ValueError("The 'ceguiSets' argument has no elements; at least one is required.")

        realType = CEGUIPropertyManager.getTypeFromCEGUITypeString(ceguiProperty.getDataType())

        ceguiSets, values, defaultValues = self.gatherData(ceguiProperty, ceguiSets)

        value = realType(values[0])
        defaultValue = realType(defaultValues[0])

        super(CEGUIPropertyWrapper, self).__init__(name = ceguiProperty.getName(),
                                                   category = ceguiProperty.getOrigin(),
                                                   helpText = ceguiProperty.getHelp(),
                                                   value = value,
                                                   defaultValue = defaultValue,
                                                   readOnly = not ceguiProperty.isWritable()
                                                   )
        self.ceguiProperty = ceguiProperty
        self.ceguiSets = ceguiSets
        self.values = values
        self.defaultValues = defaultValues
        # TODO: Can it also listen for value changes to the underlying ceguiSets' properties?

    def valueToString(self):
        if len(self.values) == 1:
            return super(CEGUIPropertyWrapper, self).valueToString()
        return "<multiple values>"

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
                "int": int,
                "float": float,
                "double": float,
                "bool": bool
                }

    @staticmethod
    def getTypeFromCEGUITypeString(ceguiStrType):
        return CEGUIPropertyManager._typeMap.get(ceguiStrType, unicode)

    @staticmethod
    def getCEGUIPropertyGUID(ceguiProperty):
        # HACK: The GUID is used as a hash value (to be able
        # to tell if two properties are the same).
        # There's currently no way to get this information, apart
        # from examining the name, datatype, origin etc. of the property
        # and build a string/hash value out of it.
        return "/".join([ceguiProperty.getOrigin(),
                         ceguiProperty.getName(),
                         ceguiProperty.getDataType()])

    def createProperty(self, ceguiProperty, ceguiSets):
        return CEGUIPropertyWrapper(ceguiProperty, ceguiSets)

    # TODO: Add a way to only show modified (non-default) or recently
    # used properties (filterbox? toggle/radio button? extra categories?)
    # TODO: Try to keep selection/scroll pos/focus when changing property sets

    def buildCategories(self, ceguiPropertySets):
        propertyList = self.buildProperties(ceguiPropertySets)
        categories = PropertyCategory.categorisePropertyList(propertyList)

        # sort properties in categories
        for cat in categories.values():
            cat.sortProperties()

        # sort categories by name
        categories = OrderedDict(sorted(categories.items(), key=lambda t: t[0]))

        return categories

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
