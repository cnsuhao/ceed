# #############################################################################
# created:    2nd July 2014
# author:     Lukas E Meindl
##############################################################################
##############################################################################
# CEED - Unified CEGUI asset editor
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
from ceed.propertytree.properties import PropertyCategory

from collections import OrderedDict

from falagard_element_editor import FalagardElementEditorProperty

import PyCEGUI


class FalagardElementAttributesManager(object):
    """Builds propertytree settings from a CEGUI Falagard element, allowing to edit its attributes in the editor.
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
        PyCEGUI.HorizontalFormatting: ct.HorizontalFormatting,
        PyCEGUI.VerticalFormatting: ct.VerticalFormatting,
        PyCEGUI.HorizontalTextFormatting: ct.HorizontalTextFormatting,
        PyCEGUI.VerticalTextFormatting: ct.VerticalTextFormatting,
        PyCEGUI.ItemListBase.SortMode: ct.SortMode,
        PyCEGUI.Colour: ct.Colour,
        PyCEGUI.ColourRect: ct.ColourRect,
        PyCEGUI.Font: ct.FontRef,
        PyCEGUI.Image: ct.ImageRef,
        PyCEGUI.BasicImage: ct.ImageRef
    }

    def __init__(self, propertyMap, visual):
        self.visual = visual
        self.propertyMap = propertyMap

    def buildCategories(self, falagardElement):
        """Create all available Properties, PropertyDefinitions and PropertyLinkDefinition options for this WidgetLook
        and categorise them.

        Return the categories, ready to be loaded into an Inspector Widget.
        """
        settingsList = self.createSettingsForFalagardElement(falagardElement)

        categories = FalagardElementSettingCategory.categorisePropertyList(settingsList)

        # sort properties in categories
        for cat in categories.values():
            cat.sortProperties()

        # sort categories by name
        categories = OrderedDict(sorted(categories.items(), key=lambda t: t[0]))

        # sort categories by name but keep some special categories on top
        def getSortKey(t):
            name, _ = t

            if name == "PropertyDefinition":
                return "000PropertyDefinition"
            elif name == "PropertyLinkDefinition":
                return "001PropertyLinkDefinition"
            elif name == "PropertyInitialiser":
                return "002PropertyInitialiser"
            else:
                return name

        return OrderedDict(sorted(categories.items(), key=getSortKey))

    def addSettingForPropertyDefinitionBaseType(self, propertyDefBaseObject, widgetLookObject, category, listOfWidgetLookSettings):
        """
        Creates a setting for a PropertyDefinition or PropertyLinkDefinition of a WidgetLook and adds it to a list of settings
        :param propertyDefBaseObject: PyCEGUI.PropertyDefinitionBase
        :param widgetLookObject: PyCEGUI.WidgetLookFeel
        :param listOfWidgetLookSettings: list
        :return:
        """

        propertyName = propertyDefBaseObject.getPropertyName()
        dataType = propertyDefBaseObject.getDataType()
        initialValue = propertyDefBaseObject.getInitialValue()
        helpString = propertyDefBaseObject.getHelpString()

        value, propertyType, editorOptions = self.retrieveValueAndPropertyType(self.propertyMap, category, propertyName, dataType, initialValue, True)
        defaultValue = value

        newSetting = self.createWidgetLookFeelPropertySetting(value, defaultValue, propertyType, editorOptions, propertyDefBaseObject, propertyName, category,
                                                              helpString)

        listOfWidgetLookSettings.append(newSetting)

    def addSettingForPropertyInitialiserType(self, propertyInitialiser, widgetLookObject, listOfWidgetLookSettings, dummyWindow):
        """
        Creates a setting for a PropertyInitialiser of a WidgetLook and adds it to a list of settings
        :param propertyInitialiser: PyCEGUI.PropertyInitialiser
        :param widgetLookObject: PyCEGUI.WidgetLookFeel
        :param listOfWidgetLookSettings: list
        :param dummyWindow: PyCEGUI.Window
        :return:
        """

        category = "PropertyInitialiser"

        propertyName = propertyInitialiser.getTargetPropertyName()
        initialValue = propertyInitialiser.getInitialiserValue()

        propertyInstance = dummyWindow.getPropertyInstance(propertyName)

        dataType = propertyInstance.getDataType()
        helpString = propertyInstance.getHelp()

        if initialValue is u"":
            initialValue = None

        value, propertyType, editorOptions = self.retrieveValueAndPropertyType(self.propertyMap, category, propertyName, dataType, initialValue, True)
        defaultValue = value

        from falagard_element_interface import FalagardElementInterface

        getterCallback = FalagardElementInterface.getAttributeValue
        setterCallback = FalagardElementInterface.setAttributeValue
        newSetting = self.createWidgetLookFeelPropertySetting(value, defaultValue, propertyType, editorOptions, widgetLookObject, propertyName, category,
                                                              helpString, getterCallback, setterCallback)

        listOfWidgetLookSettings.append(newSetting)

    @staticmethod
    def retrieveValueAndPropertyType(propertyMap, category, propertyName, dataType, currentValue, isProperty):
        """
        Returns an adjusted value and propertyType and editorOptions, using a propertyMap. Converts the value to the right internal python class for the given cegui type.
        :param propertyMap:
        :param category:
        :param propertyName:
        :param dataType:
        :param currentValue:
        :return: value and propertyType
        """

        editorOptions = None

        # if the current property map specifies a different type, use that one instead
        pmEntry = propertyMap.getEntry(category, propertyName)
        if pmEntry and pmEntry.typeName:
            dataType = pmEntry.typeName

        # Retrieve the EditorSettings if available
        if pmEntry and pmEntry.editorSettings:
            editorOptions = pmEntry.editorSettings

        if isProperty:
            # get a native data type for the CEGUI data type string, falling back to string
            from ceed.propertysetinspector import CEGUIPropertyManager

            pythonDataType = CEGUIPropertyManager.getTypeFromCEGUITypeString(dataType)
        else:
            # get a native data type for the CEGUI data type, falling back to string
            pythonDataType = FalagardElementAttributesManager.getTypeFromCEGUIType(dataType)

        # get the callable that creates this data type
        # and the Property type to use.
        if issubclass(pythonDataType, ct.Base):
            # if it is a subclass of our ceguitypes, do some special handling
            value = pythonDataType.fromString(pythonDataType.toString(currentValue))
            propertyType = pythonDataType.getPropertyType()
        else:
            if currentValue is None:
                value = None
            elif pythonDataType is bool:
                # The built-in bool parses "false" as True
                # so we replace the default value creator.
                value = ptUtility.boolFromString(currentValue)
            else:
                value = pythonDataType(currentValue)

            propertyType = properties.Property

        return value, propertyType, editorOptions

    def createWidgetLookFeelPropertySetting(self, value, defaultValue, propertyType, editorOptions, widgetLookObject, propertyName, category, helpString):
        """Create one MultiPropertyWrapper based property for a specified WidgetLookFeel's PropertyInitialiser, PropertyDefinition or PropertyLinkDefinition
        """

        # Create and return the new Property
        return FalagardElementEditorProperty(name=propertyType,
                                              category=category,
                                              helpText=helpString,
                                              value=value,
                                              defaultValue=defaultValue,
                                              readOnly=False,
                                              editorOptions=editorOptions,
                                              visual=self.visual,
                                              falagardElement=widgetLookObject,
                                              attributeName=propertyName)

    def createSettingsForFalagardElement(self, falagardElement):
        """
        Creates a list of settings for any type of Falagard Element (except the WidgetLookFeel itself)
        :param falagardElement:
        :return:
        """

        settings = []

        if falagardElement is None:
            return settings

        from falagard_element_interface import FalagardElementInterface

        attributeList = FalagardElementInterface.getListOfAttributes(falagardElement)

        for attributeName in attributeList:
            attribute = FalagardElementInterface.getAttributeValue(falagardElement, attributeName)
            newSetting = self.createEditorPropertyForFalagardElement(falagardElement, attributeName, attribute, "")
            settings.append(newSetting)

        return settings

    @staticmethod
    def getTypeFromCEGUIType(ceguiType):
        # Returns a corresponding python type for a given CEGUI type
        return FalagardElementAttributesManager._typeMap.get(ceguiType, unicode)

    def createEditorPropertyForFalagardElement(self, falagardElement, attributeName, attribute, helpText):
        """Create one MultiPropertyWrapper based property for a specified FalagardElement's attribute (which can be an XML attribute or a child element)
        """

        # Get the CEGUI type for the attribute
        attributeDataType = type(attribute)

        from tabbed_editor import LookNFeelTabbedEditor

        falagardElementTypeStr = LookNFeelTabbedEditor.getFalagardElementTypeAsString(falagardElement)

        value, propertyType, editorOptions = self.retrieveValueAndPropertyType(self.propertyMap, falagardElementTypeStr, attributeName, attributeDataType, attribute, False)
        defaultValue = value

        if attributeName == "look" and falagardElementTypeStr == "SectionSpecification" and value:
            from ceed.editors.looknfeel.tabbed_editor import LookNFeelTabbedEditor

            value, widgetLookEditorID = LookNFeelTabbedEditor.unmapMappedNameIntoOriginalParts(value)
            defaultValue = value

        # create and return the multi wrapper
        return FalagardElementEditorProperty(name=attributeName,
                                             category=falagardElementTypeStr,
                                             helpText=helpText,
                                             value=value,
                                             defaultValue=defaultValue,
                                             readOnly=False,
                                             editorOptions=editorOptions,
                                             visual=self.visual,
                                             falagardElement=falagardElement,
                                             attributeName=attributeName)

class FalagardElementSettingCategory(object):
    """ A category for Falagard element settings.
    Categories have a name and hold a list of settings.
    """

    def __init__(self, name):
        """Initialise the instance with the specified name."""
        self.name = name
        self.properties = OrderedDict()

    @staticmethod
    def categorisePropertyList(propertyList, unknownCategoryName="Unknown"):
        """Given a list of settings, creates categories and adds the
        settings to them based on their 'category' field.

        The unknownCategoryName is used for a category that holds all
        properties that have no 'category' specified.
        """
        categories = {}
        for prop in propertyList:
            catName = prop.category if prop.category else unknownCategoryName
            if not catName in categories:
                categories[catName] = FalagardElementSettingCategory(catName)
            category = categories[catName]
            category.properties[prop.name] = prop

        return categories

    def sortProperties(self, reverse=False):
        """ We want to maintain the order used by the FalagardElement interface
        :param reverse:
        :return:
        """
        self.properties = OrderedDict(self.properties.items())