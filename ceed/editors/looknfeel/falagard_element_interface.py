# #############################################################################
# created:    5th July 2014
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


import PyCEGUI


class FalagardElementInterface(object):
    """ Implements static functions that can be used to get an set the
    attributes of Falagard elements. Also contains a list of all attributes
    for each type of Falagard element.
    """



    @staticmethod
    def getListOfAttributes(falagardElement):
        """
        Returns a list of names of attributes for a given Falagard element. Children elements, which can only exist a maximum of one time, are also added to the list. The list
        can be used in connection with getAttributeValue and setAttributeValue.
        :param falagardElement:
        :return:
        """

        NAMED_AREA_ATTRIBUTES = ["name"]
        IMAGERY_SECTION_ATTRIBUTES = ["name", "Colour", "ColourProperty"]
        STATE_IMAGERY_ATTRIBUTES = ["name", "clipped"]
        WIDGET_COMPONENT_ATTRIBUTES = ["nameSuffix", "type", "renderer", "look", "autoWindow", "VertAlignment", "HorzAlignment"]
        IMAGERY_COMPONENT_ATTRIBUTES = ["Image", "ImageProperty", "Colour", "ColourProperty", "VertFormat", "VertFormatProperty", "HorzFormat", "HorzFormatProperty"]
        TEXT_COMPONENT_ATTRIBUTES = ["Text", "TextProperty", "Font", "FontProperty", "Colour", "ColourProperty", "VertFormat", "VertFormatProperty", "HorzFormat", "HorzFormatProperty"]
        FRAME_COMPONENT_ATTRIBUTES = ["Colour", "ColourProperty"]
        LAYER_SPECIFICATION_ATTRIBUTES = ["priority"]
        SECTION_SPECIFICATION_ATTRIBUTES = ["section", "look", "controlProperty", "controlValue", "controlWidget", "Colour", "ColourProperty"]
        COMPONENT_AREA_ATTRIBUTES = ["AreaProperty", "NamedAreaSource <look>", "NamedAreaSource <name>"]

        if isinstance(falagardElement, PyCEGUI.NamedArea):
            return NAMED_AREA_ATTRIBUTES
        elif isinstance(falagardElement, PyCEGUI.ImagerySection):
            return IMAGERY_SECTION_ATTRIBUTES
        elif isinstance(falagardElement, PyCEGUI.StateImagery):
            return STATE_IMAGERY_ATTRIBUTES
        elif isinstance(falagardElement, PyCEGUI.WidgetComponent):
            return WIDGET_COMPONENT_ATTRIBUTES
        elif isinstance(falagardElement, PyCEGUI.ImageryComponent):
            return IMAGERY_COMPONENT_ATTRIBUTES
        elif isinstance(falagardElement, PyCEGUI.TextComponent):
            return TEXT_COMPONENT_ATTRIBUTES
        elif isinstance(falagardElement, PyCEGUI.FrameComponent):
            return FRAME_COMPONENT_ATTRIBUTES
        elif isinstance(falagardElement, PyCEGUI.LayerSpecification):
            return LAYER_SPECIFICATION_ATTRIBUTES
        elif isinstance(falagardElement, PyCEGUI.SectionSpecification):
            return SECTION_SPECIFICATION_ATTRIBUTES
        elif isinstance(falagardElement, PyCEGUI.ComponentArea):
            return COMPONENT_AREA_ATTRIBUTES
        else:
            return []

    @staticmethod
    def getAttributeValue(falagardElement, attributeName):
        """
        Returns an attribute value of of a Falagard element using the Falagard element's
        getter function as implemented in the CEGUI code. The attribute is identified
        by a string, which is used to determine the right function call.
        :param falagardElement:
        :param attributeName: str
        :return:
        """
        attributeList = FalagardElementInterface.getListOfAttributes(falagardElement)

        # Elements that can be children of a WidgetLookFeel:
        if isinstance(falagardElement, PyCEGUI.NamedArea):
            # "name"
            if attributeName == attributeList[0]:
                return falagardElement.getName()

        elif isinstance(falagardElement, PyCEGUI.ImagerySection):
            # "name", "Colour", "ColourProperty"
            if attributeName == attributeList[0]:
                return falagardElement.getName()
            elif attributeName == attributeList[1]:
                return falagardElement.getMasterColours()
            elif attributeName == attributeList[2]:
                return falagardElement.getMasterColoursPropertySource()

        elif isinstance(falagardElement, PyCEGUI.StateImagery):
            # "name", "clipped"
            if attributeName == attributeList[0]:
                return falagardElement.getName()
            if attributeName == attributeList[1]:
                return falagardElement.isClippedToDisplay()

        elif isinstance(falagardElement, PyCEGUI.WidgetComponent):
            # "nameSuffix", "type", "renderer", "look", "autoWindow", "VertAlignment", "HorzAlignment"
            if attributeName == attributeList[0]:
                return falagardElement.getWidgetName()
            elif attributeName == attributeList[1]:
                return falagardElement.getBaseWidgetType()
            elif attributeName == attributeList[2]:
                return falagardElement.getWindowRendererType()
            elif attributeName == attributeList[3]:
                return falagardElement.getWidgetLookName()
            elif attributeName == attributeList[4]:
                return falagardElement.isAutoWindow()
            elif attributeName == attributeList[5]:
                return falagardElement.getVerticalWidgetAlignment()
            elif attributeName == attributeList[6]:
                return falagardElement.getHorizontalWidgetAlignment()

        # Elements that can be children of an ImagerySection:
        elif isinstance(falagardElement, PyCEGUI.ImageryComponent):
            # "Image", "ImageProperty", "Colour", "ColourProperty", "VertFormat", "VertFormatProperty", "HorzFormat", "HorzFormatProperty"
            if attributeName == attributeList[0]:
                return falagardElement.getImage()
            elif attributeName == attributeList[1]:
                return falagardElement.getImagePropertySource()
            elif attributeName == attributeList[2]:
                return falagardElement.getColours()
            elif attributeName == attributeList[3]:
                return falagardElement.getColoursPropertySource()
            elif attributeName == attributeList[4]:
                return falagardElement.getVerticalFormattingFromComponent()
            elif attributeName == attributeList[5]:
                return falagardElement.getVerticalFormattingPropertySource()
            elif attributeName == attributeList[6]:
                return falagardElement.getHorizontalFormattingFromComponent()
            elif attributeName == attributeList[7]:
                return falagardElement.getHorizontalFormattingPropertySource()

        elif isinstance(falagardElement, PyCEGUI.TextComponent):
            # "Text", "Font", "TextProperty", "FontProperty", "Colour", "ColourProperty", "VertFormat", "VertFormatProperty", "HorzFormat", "HorzFormatProperty"
            if attributeName == attributeList[0]:
                return falagardElement.getText()
            elif attributeName == attributeList[1]:
                return falagardElement.getFont()
            elif attributeName == attributeList[2]:
                return falagardElement.getTextPropertySource()
            elif attributeName == attributeList[3]:
                return falagardElement.getFontPropertySource()
            elif attributeName == attributeList[4]:
                return falagardElement.getColours()
            elif attributeName == attributeList[5]:
                return falagardElement.getColoursPropertySource()
            elif attributeName == attributeList[6]:
                return falagardElement.getVerticalFormattingFromComponent()
            elif attributeName == attributeList[7]:
                return falagardElement.getVerticalFormattingPropertySource()
            elif attributeName == attributeList[8]:
                return falagardElement.getHorizontalFormattingFromComponent()
            elif attributeName == attributeList[9]:
                return falagardElement.getHorizontalFormattingPropertySource()

        elif isinstance(falagardElement, PyCEGUI.FrameComponent):
            # "Colour", "ColourProperty"
            if attributeName == attributeList[0]:
                return falagardElement.getColours()
            elif attributeName == attributeList[1]:
                return falagardElement.getColoursPropertySource()

        # Elements that can be children of a StateImagery:
        elif isinstance(falagardElement, PyCEGUI.LayerSpecification):
            if attributeName == attributeList[0]:
                return falagardElement.getLayerPriority()

        # Elements that can be children of a LayerSpecification:
        elif isinstance(falagardElement, PyCEGUI.SectionSpecification):
            # "section", "look", "controlProperty", "controlValue", "controlWidget", "Colour", "ColourProperty"
            if attributeName == attributeList[0]:
                return falagardElement.getSectionName()
            elif attributeName == attributeList[1]:
                return falagardElement.getOwnerWidgetLookFeel()
            elif attributeName == attributeList[2]:
                return falagardElement.getRenderControlPropertySource()
            elif attributeName == attributeList[3]:
                return falagardElement.getRenderControlValue()
            elif attributeName == attributeList[4]:
                return falagardElement.getRenderControlWidget()
            elif attributeName == attributeList[5]:
                return falagardElement.getOverrideColours()
            elif attributeName == attributeList[6]:
                return falagardElement.getOverrideColoursPropertySource()

        # The ComponentArea element
        elif isinstance(falagardElement, PyCEGUI.ComponentArea):
            if attributeName == attributeList[0]:
                if falagardElement.isAreaFetchedFromProperty():
                    return falagardElement.getAreaPropertySource()
                else:
                    return ""
            if attributeName == attributeList[1]:
                if falagardElement.isAreaFetchedFromNamedArea():
                    return falagardElement.getAreaPropertySource()
                else:
                    return ""
            if attributeName == attributeList[2]:
                if falagardElement.isAreaFetchedFromNamedArea():
                    return falagardElement.getNamedAreaSourceLook()
                else:
                    return ""

        # The ColourRect element
        elif isinstance(falagardElement, PyCEGUI.ColourRect):
            return []

        # The Image element
        elif isinstance(falagardElement, PyCEGUI.Image):
            return []

        raise Exception("Unknown Falagard element and/or attribute used in FalagardElementInterface.getAttributeValue")
        return None


    @staticmethod
    def setAttributeValue(falagardElement, attributeName, attributeValue):
        """
        Sets an attribute value of of a Falagard element using the Falagard element's
        getter function as implemented in the CEGUI code. The attribute is identified
        by a string, which is used to determine the right function call.
        :param falagardElement:
        :param attributeName: str
        :param attributeValue:
        :return:
        """

        attributeList = FalagardElementInterface.getListOfAttributes(falagardElement)

        # Elements that can be children of a WidgetLookFeel:
        if isinstance(falagardElement, PyCEGUI.NamedArea):
            # "name"
            if attributeName == attributeList[0]:
                return falagardElement.setName(attributeValue)

        elif isinstance(falagardElement, PyCEGUI.ImagerySection):
            # "name", "Colour", "ColourProperty"
            if attributeName == attributeList[0]:
                return falagardElement.setName(attributeValue)
            elif attributeName == attributeList[1]:
                return falagardElement.setMasterColours(attributeValue)
            elif attributeName == attributeList[2]:
                return falagardElement.setMasterColoursPropertySource(attributeValue)

        elif isinstance(falagardElement, PyCEGUI.StateImagery):
            # "name", "clipped"
            if attributeName == attributeList[0]:
                return falagardElement.setName(attributeValue)
            if attributeName == attributeList[1]:
                return falagardElement.isClippedToDisplay(attributeValue)

        elif isinstance(falagardElement, PyCEGUI.WidgetComponent):
            # "nameSuffix", "type", "renderer", "look", "autoWindow", "VertAlignment", "HorzAlignment"
            if attributeName == attributeList[0]:
                return falagardElement.setWidgetName(attributeValue)
            elif attributeName == attributeList[1]:
                return falagardElement.setBaseWidgetType(attributeValue)
            elif attributeName == attributeList[2]:
                return falagardElement.setWindowRendererType(attributeValue)
            elif attributeName == attributeList[3]:
                return falagardElement.setWidgetLookName(attributeValue)
            elif attributeName == attributeList[4]:
                return falagardElement.isAutoWindow(attributeValue)
            elif attributeName == attributeList[5]:
                return falagardElement.setVerticalWidgetAlignment(attributeValue)
            elif attributeName == attributeList[6]:
                return falagardElement.setHorizontalWidgetAlignment(attributeValue)

        # Elements that can be children of an ImagerySection:
        elif isinstance(falagardElement, PyCEGUI.ImageryComponent):
            # "Image", "ImageProperty", "Colour", "ColourProperty", "VertFormat", "VertFormatProperty", "HorzFormat", "HorzFormatProperty"
            if attributeName == attributeList[0]:
                return falagardElement.setImage(attributeValue)
            elif attributeName == attributeList[1]:
                return falagardElement.setImagePropertySource(attributeValue)
            elif attributeName == attributeList[2]:
                return falagardElement.setColours(attributeValue)
            elif attributeName == attributeList[3]:
                return falagardElement.setColoursPropertySource(attributeValue)
            elif attributeName == attributeList[4]:
                return falagardElement.setVerticalFormattingFromComponent(attributeValue)
            elif attributeName == attributeList[5]:
                return falagardElement.setVerticalFormattingPropertySource(attributeValue)
            elif attributeName == attributeList[6]:
                return falagardElement.setHorizontalFormattingFromComponent(attributeValue)
            elif attributeName == attributeList[7]:
                return falagardElement.setHorizontalFormattingPropertySource(attributeValue)

        elif isinstance(falagardElement, PyCEGUI.TextComponent):
            # "Text", "Font", "TextProperty", "FontProperty", "Colour", "ColourProperty", "VertFormat", "VertFormatProperty", "HorzFormat", "HorzFormatProperty"
            if attributeName == attributeList[0]:
                return falagardElement.setText(attributeValue)
            elif attributeName == attributeList[1]:
                return falagardElement.setFont(attributeValue)
            elif attributeName == attributeList[2]:
                return falagardElement.setTextPropertySource(attributeValue)
            elif attributeName == attributeList[3]:
                return falagardElement.setFontPropertySource(attributeValue)
            elif attributeName == attributeList[4]:
                return falagardElement.setColours(attributeValue)
            elif attributeName == attributeList[5]:
                return falagardElement.setColoursPropertySource(attributeValue)
            elif attributeName == attributeList[6]:
                return falagardElement.setVerticalFormattingFromComponent(attributeValue)
            elif attributeName == attributeList[7]:
                return falagardElement.setVerticalFormattingPropertySource(attributeValue)
            elif attributeName == attributeList[8]:
                return falagardElement.setHorizontalFormattingFromComponent(attributeValue)
            elif attributeName == attributeList[9]:
                return falagardElement.setHorizontalFormattingPropertySource(attributeValue)

        elif isinstance(falagardElement, PyCEGUI.FrameComponent):
            # "Colour", "ColourProperty",
            if attributeName == attributeList[0]:
                return falagardElement.setColours(attributeValue)
            elif attributeName == attributeList[1]:
                return falagardElement.setColoursPropertySource(attributeValue)

        # Elements that can be children of a StateImagery:
        elif isinstance(falagardElement, PyCEGUI.LayerSpecification):
            if attributeName == attributeList[0]:
                return falagardElement.setLayerPriority(attributeValue)

        # Elements that can be children of a LayerSpecification:
        elif isinstance(falagardElement, PyCEGUI.SectionSpecification):
            # "section", "look", "controlProperty", "controlValue", "controlWidget", "Colour", "ColourProperty"
            if attributeName == attributeList[0]:
                return falagardElement.setSectionName(attributeValue)
            elif attributeName == attributeList[1]:
                return falagardElement.setOwnerWidgetLookFeel(attributeValue)
            elif attributeName == attributeList[2]:
                return falagardElement.setRenderControlPropertySource(attributeValue)
            elif attributeName == attributeList[3]:
                return falagardElement.setRenderControlValue(attributeValue)
            elif attributeName == attributeList[4]:
                return falagardElement.setRenderControlWidget(attributeValue)
            elif attributeName == attributeList[5]:
                return falagardElement.setOverrideColours(attributeValue)
            elif attributeName == attributeList[6]:
                return falagardElement.setOverrideColoursPropertySource(attributeValue)

        # The ComponentArea element
        elif isinstance(falagardElement, PyCEGUI.ComponentArea):
            if attributeName == attributeList[0]:
                falagardElement.setAreaPropertySource(attributeValue)
            if attributeName == attributeList[1]:
                falagardElement.setAreaPropertySource(attributeValue)
            if attributeName == attributeList[2]:
                falagardElement.setNamedAreaSouce(attributeValue, falagardElement.getAreaPropertySource())

        # The ColourRect element
        elif isinstance(falagardElement, PyCEGUI.ColourRect):
            return

        # The Image element
        elif isinstance(falagardElement, PyCEGUI.Image):
            return

        else:
            raise Exception("Unknown Falagard element and/or attribute used in FalagardElementInterface.setAttributeValue")