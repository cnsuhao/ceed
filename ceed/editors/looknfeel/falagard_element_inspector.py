##############################################################################
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

        categories = properties.PropertyCategory.categorisePropertyList(settingsList)

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

    def createSettingsForFalagardElement(self, falagardElement):
        """
        Create and return all available settings for the Falagard Element

        :param falagardElement:
        :return:
        """
        if falagardElement is None:
            return []

        # If the Falagard Element is the WidgetLookFeel itself:
        elif isinstance(falagardElement, PyCEGUI.WidgetLookFeel):
            return self.createSettingsForWidgetLookFeel(falagardElement)
        # For all other Falagard Elements (child elements of the WidgetLook):
        else:
            return self.createSettingsForNonWidgetLookElement(falagardElement)

    def createSettingsForWidgetLookFeel(self, widgetLookObject):
        """
        Creates a list of settings for a specificed WidgetLookFeel object, based on all its child elements of type Property, PropertyDefinition and PropertyLinkDefinition

        :param widgetLookObject: PyCEGUI.WidgetLookFeel
        :return: list
        """

        listOfWidgetLookSettings = []

        dummyWindow = PyCEGUI.WindowManager.getSingleton().createWindow(widgetLookObject.getName(), "")

        self.createSettingsForPropertyDefinitions(widgetLookObject, listOfWidgetLookSettings, dummyWindow)
        self.createSettingsForPropertyLinkDefinitions(widgetLookObject, listOfWidgetLookSettings, dummyWindow)
        self.createSettingsForPropertyInitialisers(widgetLookObject, listOfWidgetLookSettings, dummyWindow)

        PyCEGUI.WindowManager.getSingleton().destroyWindow(dummyWindow)

        return listOfWidgetLookSettings

    def createSettingsForPropertyDefinitions(self, widgetLookObject, listOfWidgetLookSettings, dummyWindow):
        """
        Creates settings for the PropertyDefinitions of a WidgetLook and adds them to a list of settings
        :param widgetLookObject: PyCEGUI.WidgetLookFeel
        :param listOfWidgetLookSettings: list
        :param dummyWindow: PyCEGUI.Window
        :return:
        """

        propDefNames = widgetLookObject.getPropertyDefinitionNames(True)
        propertyDefMap = widgetLookObject.getPropertyDefinitionMap(True)

        for propDefName in propDefNames:
            propertyDef = PyCEGUI.Workarounds.PropertyDefinitionBaseMapGet(propertyDefMap, propDefName)
            propertyName = propertyDef.getPropertyName()
            dataType = propertyDef.getDataType()
            initialValue = propertyDef.getInitialValue()
            category = "PropertyDefinition"
            helpString = propertyDef.getHelpString()

            if initialValue is u"":
                initialValue = None

            listOfWidgetLookSettings.append(self.createWidgetLookFeelPropertySetting(widgetLookObject, propertyName, dataType, initialValue, category,
                                                                                     helpString, False, self.propertyMap))

    def createSettingsForPropertyLinkDefinitions(self, widgetLookObject, listOfWidgetLookSettings, dummyWindow):
        """
        Creates settings for the PropertyLinkDefinitions of a WidgetLook and adds them to a list of settings
        :param widgetLookObject: PyCEGUI.WidgetLookFeel
        :param listOfWidgetLookSettings: list
        :param dummyWindow: PyCEGUI.Window
        :return:
        """

        propLinkDefNames = widgetLookObject.getPropertyLinkDefinitionNames(True)
        propertyLinkDefMap = widgetLookObject.getPropertyLinkDefinitionMap(True)
        for propLinkDefName in propLinkDefNames:
            propertyLinkDef = PyCEGUI.Workarounds.PropertyDefinitionBaseMapGet(propertyLinkDefMap, propLinkDefName)

            dataType = propertyLinkDef.getDataType()
            initialValue = propertyLinkDef.getInitialValue()
            category = "PropertyLinkDefinition"
            helpString = propertyLinkDef.getHelpString()

            if initialValue is u"":
                initialValue = None

            listOfWidgetLookSettings.append(self.createWidgetLookFeelPropertySetting(widgetLookObject, propLinkDefName, dataType, initialValue, category,
                                                                                     helpString, False, self.propertyMap))

    def createSettingsForPropertyInitialisers(self, widgetLookObject, listOfWidgetLookSettings, dummyWindow):
        """
        Creates settings for the PropertyInitialisers of a WidgetLook and adds them to a list of settings
        :param widgetLookObject: PyCEGUI.WidgetLookFeel
        :param listOfWidgetLookSettings: list
        :param dummyWindow: PyCEGUI.Window
        :return:
        """

        propertyInitialiserNames = widgetLookObject.getPropertyInitialiserNames(True)
        propertyInitialiserMap = widgetLookObject.getPropertyInitialiserMap(True)
        for propertyInitialiserName in propertyInitialiserNames:
            propertyInitialiser = PyCEGUI.Workarounds.PropertyInitialiserMapGet(propertyInitialiserMap, propertyInitialiserName)

            propertyName = propertyInitialiser.getTargetPropertyName()
            initialValue = propertyInitialiser.getInitialiserValue()
            category = "PropertyInitialiser"

            propertyInstance = dummyWindow.getPropertyInstance(propertyName)

            dataType = propertyInstance.getDataType()
            helpString = propertyInstance.getHelp()

            if initialValue is u"":
                initialValue = None

            listOfWidgetLookSettings.append(self.createWidgetLookFeelPropertySetting(widgetLookObject, propertyName, dataType, initialValue, category,
                                                                                     helpString, False, self.propertyMap))

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

    def createWidgetLookFeelPropertySetting(self, widgetLookObject, propertyName, dataType, currentValue, category, helpString, readOnly, propertyMap):
        """Create one MultiPropertyWrapper based property for the CEGUI Property
        for all of the PropertySets specified.
        """

        value, propertyType, editorOptions = self.retrieveValueAndPropertyType(propertyMap, category, propertyName, dataType, currentValue, True)
        defaultValue = value

        # create the inner properties;
        # one property for each CEGUI PropertySet
        innerProperties = []
        innerProperty = propertyType(name=propertyName,
                                     category=category,
                                     helpText=helpString,
                                     value=value,
                                     defaultValue=defaultValue,
                                     readOnly=readOnly,
                                     createComponents=False
                                     )
        innerProperties.append(innerProperty)

        # create the template property;
        # this is the property that will create the components
        # and it will be edited.
        templateProperty = propertyType(name=propertyName,
                                        category=category,
                                        helpText=helpString,
                                        value=value,
                                        defaultValue=defaultValue,
                                        readOnly=readOnly,
                                        editorOptions=editorOptions
                                        )

        # create FalagardElement MultiPropertyWrapper
        return FalagardElementMultiPropertyWrapper(templateProperty, innerProperties, True,
                                                   self.visual, widgetLookObject, propertyName)

    def createSettingsForNonWidgetLookElement(self, falagardElement):
        """
        Creates a list of settings for any type of Falagard Element (except the WidgetLookFeel itself)
        :param falagardElement:
        :return:
        """
        settings = []

        from falagard_element_interface import FalagardElementInterface

        attributeList = FalagardElementInterface.getListOfAttributes(falagardElement)

        for attributeName in attributeList:
            attribute = FalagardElementInterface.getAttributeValue(falagardElement, attributeName)
            newSetting = self.createPropertyForFalagardElement(falagardElement, attributeName, attribute, "")
            settings.append(newSetting)

        return settings

    @staticmethod
    def getTypeFromCEGUIType(ceguiType):
        # Returns a corresponding python type for a given CEGUI type
        return FalagardElementAttributesManager._typeMap.get(ceguiType, unicode)

    def createPropertyForFalagardElement(self, falagardElement, attributeName, attribute, helpText):
        """Create one MultiPropertyWrapper based property for the CEGUI Property
        for all of the PropertySets specified.
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