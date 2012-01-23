from collections import OrderedDict

from .qtwidgets import LineEditWithClearButton

from .propertytree.properties import Property
from .propertytree.properties import PropertyCategory
from .propertytree.properties import MultiPropertyWrapper

from .propertytree.ui import PropertyTreeWidget

from ceed.cegui import ceguitypes as ct

from PySide.QtGui import QWidget
from PySide.QtGui import QVBoxLayout

from PySide.QtCore import QSize

class PropertyInspectorWidget(QWidget):
    """Full blown inspector widget for CEGUI PropertySet(s).
    
    Requires a call to 'setPropertyManager()' before
    it can show properties via 'setPropertySets'.
    """

    # TODO: Add a way to only show modified (non-default) or recently
    # used properties (filterbox? toggle/radio button? extra categories?)

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

        # set the minimum size to a reasonable value for this widget
        self.setMinimumSize(200, 200)

        self.propertyManager = None

    def sizeHint(self):
        # we'd rather have this size
        return QSize(400, 600)

    def filterChanged(self, filterText):
        self.ptree.setFilter(filterText)

    def setPropertyManager(self, propertyManager):
        self.propertyManager = propertyManager

    def setPropertySets(self, ceguiPropertySets):
        categories = self.propertyManager.buildCategories(ceguiPropertySets)

        # load them into the tree
        self.ptree.load(categories)

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
                "uint": int,
                "float": float,
                "bool": bool,
                "String": unicode,
                "USize": ct.USize
                }
    #===============================================================================
    # TODO: AspectMode
    # TODO: Font*
    # TODO: HorizontalAlignment
    # TODO: Image*
    # TODO: Quaternion
    # TODO: UBox
    # TODO: Unknown
    # TODO: URect
    # TODO: UVector2
    # TODO: VerticalAlignment
    # TODO: WindowUpdateMode
    #===============================================================================

    @staticmethod
    def getTypeFromCEGUITypeString(ceguiStrType):
        #print "TODO: " + ceguiStrType
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

    def __init__(self, propertyMap):
        self.propertyMap = propertyMap

    def createProperty(self, ceguiProperty, ceguiSets, multiWrapperType=MultiPropertyWrapper):
        name = ceguiProperty.getName()
        category = ceguiProperty.getOrigin()
        helpText = ceguiProperty.getHelp()
        readOnly = not ceguiProperty.isWritable()

        propertyDataType = ceguiProperty.getDataType()
        pmEntry = self.propertyMap.getEntry(category, name)
        if pmEntry and pmEntry.typeName:
            propertyDataType = pmEntry.typeName

        pythonDataType = self.getTypeFromCEGUITypeString(propertyDataType)

        valueCreator = None
        propertyType = None
        if issubclass(pythonDataType, ct.Base):
            valueCreator = pythonDataType.fromString
            propertyType = pythonDataType.getPropertyType()
        else:
            valueCreator = pythonDataType
            propertyType = Property

        value = None
        defaultValue = None

        innerProperties = []
        for ceguiSet in ceguiSets:
            assert ceguiSet.isPropertyPresent(name), "Property '%s' was not found in PropertySet." % name
            value = valueCreator(ceguiProperty.get(ceguiSet))
            defaultValue = valueCreator(ceguiProperty.getDefault(ceguiSet))

            innerProperty = propertyType(name = name,
                                         category = category,
                                         helpText = helpText,
                                         value = value,
                                         defaultValue = defaultValue,
                                         readOnly = readOnly,
                                         createComponents = False
                                         )
            innerProperties.append(innerProperty)

            # hook the inner callback (the 'cb' function) to
            # the value changed notification of the cegui propertyset
            # so that we update our value(s) when the propertyset's
            # property changes because of another editor (i.e. visual, undo, redo)
            def makeCallback(cs, cp, ip):
                def cb():
                    ip.setValue(valueCreator(cp.get(cs)))
                return cb
            ceguiSet.propertyManagerCallbacks[name] = makeCallback(ceguiSet, ceguiProperty, innerProperty)

        editorOptions = None
        if pmEntry and pmEntry.editorSettings:
            editorOptions = pmEntry.editorSettings
        templateProperty = propertyType(name = name,
                                        category = category,
                                        helpText = helpText,
                                        value = value,
                                        defaultValue = defaultValue,
                                        readOnly = readOnly,
                                        editorOptions = editorOptions
                                        )

        multiProperty = multiWrapperType(templateProperty, innerProperties, True)

        return multiProperty

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

            # add a custom attribute to the PropertySet.
            # this will be filled later on with callbacks (see
            # 'createProperty'), one for each property that
            # will be called when the properties of the set change.
            # it's OK to clear any previous value because we only
            # use this internally and we only need a max of one 'listener'
            # for each property.
            # It's not pretty but it does the job well enough.
            setattr(cgSet, "propertyManagerCallbacks", dict())

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
                    if cgProp.isReadable():
                        #print "XXX: {}/{}/{}".format(cgProp.getOrigin(), cgProp.getName(), cgProp.getDataType())
                        # check mapping and ignore hidden properties
                        pmEntry = self.propertyMap.getEntry(cgProp.getOrigin(), cgProp.getName())
                        if (not pmEntry) or (not pmEntry.hidden):
                            cgProps[guid] = (cgProp, [cgSet])

                propIt.next()

        # Convert the CEGUI properties with their sets to property tree properties.
        ptProps = [self.createProperty(cgProp, sets) for cgProp, sets in cgProps.values()]

        return ptProps
