# #############################################################################
# created:    2nd July 2014
# author:     Lukas E Meindl
# #############################################################################
##############################################################################
#   CEED - Unified CEGUI asset editor
#
#   Copyright (C) 2011-2014   Martin Preisler <martin@preisler.me>
#                             and contributing authors (see AUTHORS file)
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
###############################################################################

from ceed.propertytree import properties
from ceed.propertytree import utility as ptUtility

from ceed.cegui import ceguitypes as ct

from collections import OrderedDict

from falagard_element_editor import FalagardElementMultiPropertyWrapper

import PyCEGUI


class FalagardElementAttributesManager(object):
    """Builds propertytree properties from a CEGUI WidgetLook offering options to modify its Properties, PropertyDefinitions and PropertyLinkDefinitions,
    by using a PropertyMap.
    """

    # Maps CEGUI data types (in string form) to Python types

    _typeMap = {
        int: int,
        float: float,
        bool: bool,
        unicode: unicode,
        PyCEGUI.USize: ct.USize,
        PyCEGUI.UVector2: ct.UVector2,
        PyCEGUI.URect: ct.URect,
        PyCEGUI.AspectMode: ct.AspectMode,
        PyCEGUI.HorizontalAlignment: ct.HorizontalAlignment,
        PyCEGUI.VerticalAlignment: ct.VerticalAlignment,
        PyCEGUI.WindowUpdateMode: ct.WindowUpdateMode,
        PyCEGUI.Quaternion: ct.Quaternion,
        PyCEGUI.HorizontalTextFormatting: ct.HorizontalTextFormatting,
        PyCEGUI.VerticalTextFormatting: ct.VerticalTextFormatting,
        PyCEGUI.ItemListBase.SortMode: ct.SortMode,
        PyCEGUI.Colour: ct.Colour,
        PyCEGUI.ColourRect: ct.ColourRect,
        PyCEGUI.Font: ct.FontRef,
        PyCEGUI.Image: ct.ImageRef,
        PyCEGUI.BasicImage: ct.ImageRef
    }
    # TODO: Font*, Image*, UBox?

    def __init__(self, propertyMap, visual):
        self.visual = visual
        self.propertyMap = propertyMap

    def buildCategories(self, falagardElement):
        """Create all available Properties, PropertyDefinitions and PropertyLinkDefinition options for this WidgetLook
        and categorise them.

        Return the categories, ready to be loaded into an Inspector Widget.
        """
        settingsList = self.createSettingsForFalagardElement(falagardElement)

        categories = properties.PropertyCategory.categorisePropertyList(settingsList)

        # sort properties in categories
        for cat in categories.values():
            cat.sortProperties()

        # sort categories by name
        categories = OrderedDict(sorted(categories.items(), key=lambda t: t[0]))

        # sort categories by name but keep some special categories on top
        def getSortKey(t):
            name, _ = t

            if name == "Element":
                return "000Element"
            elif name == "NamedElement":
                return "001NamedElement"
            elif name == "Window":
                return "002Window"
            elif name.startswith("CEGUI/"):
                return name[6:]
            elif name == "Unknown":
                return "ZZZUnknown"
            else:
                return name

        return OrderedDict(sorted(categories.items(), key=getSortKey))

    def createSettingsForFalagardElement(self, falagardElement):
        """
        :param falagardElement:
        :return:
        """

        """Create and return all available settings for the Falagard Element"""

        # add a custom attribute to the PropertySet.
        # this will be filled later on with callbacks (see
        # 'createProperty'), one for each property that
        # will be called when the properties of the set change.
        # it's OK to clear any previous value because we only
        # use this internally and we only need a max of one 'listener'
        # for each property.
        # It's not pretty but it does the job well enough.

        if falagardElement is None:
            return []

        elif isinstance(falagardElement, PyCEGUI.WidgetLookFeel):
            return self.createSettingsForWidgetLookFeel(falagardElement)
        # All other Falagard Elements:
        else:
            return self.createSettingsForNonWidgetLookElement(falagardElement)

    @staticmethod
    def createSettingsForWidgetLookFeel(widgetLookObject):
        """

        :param widgetLookObject: PyCEGUI.WidgetLookFeel
        :return: list
        """

        """ TODO: FIX
        propertyDefs = widgetLookObject.getPropertyDefinitions()

        for propertyDefinition in propertyDefs:
            prop = type(PyCEGUI.Property)(propertyDefinition)
            type2 = prop.getDataType()

            uga = dir(propertyDefinition)



        definitions = widgetLookObject.getPropertyDefinitionIterator()
        propDefIterator = definitions.isAtEnd()
        while not propDefIterator == definitions.end():
            prop = propDefIterator.clone()
            propDefIterator.next()


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
                    #print("XXX: {}/{}/{}".format(cgProp.getOrigin(), cgProp.getName(), cgProp.getDataType()))
                    # check mapping and ignore hidden properties
                    pmEntry = self.propertyMap.getEntry(cgProp.getOrigin(), cgProp.getName())
                    if (not pmEntry) or (not pmEntry.hidden):
                        cgProps[guid] = (cgProp, [widgetLookObject])

            propIt.next()

        """
        return []

    def createSettingsForNonWidgetLookElement(self, falagardElement):
        """
        Creates properties for the
        :param falagardElement:
        :return:
        """
        settings = []

        from falagard_element_interface import FalagardElementInterface
        attributeList = FalagardElementInterface.getListOfAttributes(falagardElement)

        for attributeName in attributeList:
            attribute = FalagardElementInterface.getAttributeValue(falagardElement, attributeName)
            newSetting = self.createProperty(falagardElement, attributeName, attribute, "")
            settings.append(newSetting)

        return settings

    @staticmethod
    def getTypeFromCEGUIType(ceguiType):
        # Returns a corresponding python type for a given CEGUI type
        return FalagardElementAttributesManager._typeMap.get(ceguiType, unicode)

    def createProperty(self, falagardElement, attributeName, attribute, helpText):
        """Create one MultiPropertyWrapper based property for the CEGUI Property
        for all of the PropertySets specified.
        """

        # Get the CEGUI type for the attribute
        attributeDataType = type(attribute)

        from tabbed_editor import LookNFeelTabbedEditor
        falagardElementTypeStr = LookNFeelTabbedEditor.getFalagardElementTypeAsString(falagardElement)

        # if the current property map specifies a different type, use that one instead
        pmEntry = self.propertyMap.getEntry(falagardElementTypeStr, attributeName)
        if pmEntry and pmEntry.typeName:
            attributeDataType = pmEntry.typeName
        # get a native data type for the CEGUI data type, falling back to string
        pythonDataType = self.getTypeFromCEGUIType(attributeDataType)

        # get the callable that creates this data type
        # and the Property type to use.
        if issubclass(pythonDataType, ct.Base):
            # if it is a subclass of our ceguitypes, do some special handling
            value = pythonDataType.fromString(pythonDataType.toString(attribute))
            propertyType = pythonDataType.getPropertyType()
        else:
            if pythonDataType is bool:
                # The built-in bool parses "false" as True
                # so we replace the default value creator.
                value = ptUtility.boolFromString
            else:
                value = pythonDataType(attribute)
            propertyType = properties.Property

        defaultValue = value

        innerProperty = propertyType(name=attributeName,
                                     category=falagardElementTypeStr,
                                     helpText=helpText,
                                     value=value,
                                     defaultValue=defaultValue,
                                     readOnly=False,
                                     createComponents=False  # no need for components, the template will provide these
                                     )

        innerProperties = [innerProperty]

        # create the template property;
        # this is the property that will create the components
        # and it will be edited.
        editorOptions = None
        if pmEntry and pmEntry.editorSettings:
            editorOptions = pmEntry.editorSettings
        templateProperty = propertyType(name=attributeName,
                                        category=falagardElementTypeStr,
                                        helpText=helpText,
                                        value=value,
                                        defaultValue=defaultValue,
                                        readOnly=False,
                                        editorOptions=editorOptions)

        # create and return the multi wrapper
        return FalagardElementMultiPropertyWrapper(templateProperty, innerProperties, True,
                                                   self.visual, falagardElement, attributeName)