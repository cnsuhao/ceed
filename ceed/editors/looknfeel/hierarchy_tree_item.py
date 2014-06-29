##############################################################################
#   created:    25th June 2014
#   author:     Lukas E Meindl
##############################################################################
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
##############################################################################

from PySide import QtCore
from PySide import QtGui

import PyCEGUI

class LookNFeelHierarchyItem(QtGui.QStandardItem):

    def __init__(self, widgetLookElement):
        """
        Creates a hierarchy item based on an element of the WidgetLookFeel object. The element can be
        WidgetLookFeel itself or any child node (such as StateImagery or NamedArea, etc.) that is contained
        in the WidgetLookFeel or any of its children. The children of this element will created as well. The
        resulting hierarchy will be equal, or at least very similar, to the node hierarchy seen in the XML file.
        :param widgetLookElement:
        :return:
        """

        self.widgetLookElement = widgetLookElement
        name, toolTip = self.getNameAndToolTip(widgetLookElement)

        super(LookNFeelHierarchyItem, self).__init__(name)
        self.setToolTip(toolTip)

        self.setFlags(QtCore.Qt.ItemIsEnabled |
                      QtCore.Qt.ItemIsSelectable)

        self.setData(None, QtCore.Qt.CheckStateRole)

        self.createChildren()

    @staticmethod
    def getNameAndToolTip(widgetLookElement):
        """
        Creates a name and tooltip for any element that can be part of a WidgetLookFeel and returns it
        :param widgetLookElement:
        :return: str, str
        """
        name = u"None"
        toolTip = u"type: None"

        # The WidgetLookFeel object:
        if isinstance(widgetLookElement, PyCEGUI.WidgetLookFeel):
            from ceed.editors.looknfeel.tabbed_editor import LookNFeelTabbedEditor
            name = "Properties, PropertyDefinitions, PropertyLinkDefinitions"
            toolTip = u"type: Property, PropertyDefinition, PropertyLinkDefinition"

        # Objects that can be owned by a WidgetLookFeel:
        elif isinstance(widgetLookElement, PyCEGUI.NamedArea):
            name = u"NamedArea: \"" + widgetLookElement.getName() + u"\""
            toolTip = u"type: NamedArea"
        elif isinstance(widgetLookElement, PyCEGUI.ImagerySection):
            name = u"ImagerySection: \"" + widgetLookElement.getName() + u"\""
            toolTip = u"type: ImagerySection"
        elif isinstance(widgetLookElement, PyCEGUI.StateImagery):
            name = u"StateImagery: \"" + widgetLookElement.getName() + u"\""
            toolTip = u"type: StateImagery"
        elif isinstance(widgetLookElement, PyCEGUI.WidgetComponent):
            name = u"Child: \"" + widgetLookElement.getName() + u"\" type: " + widgetLookElement.getWidgetLookName() + u""
            toolTip = u"type: WidgetComponent"

        # Objects that can be owned by a ImagerySection:
        elif isinstance(widgetLookElement, PyCEGUI.ImageryComponent):
            name = u"ImageryComponent"
            toolTip = u"type: ImageryComponent"
        elif isinstance(widgetLookElement, PyCEGUI.TextComponent):
            name = u"TextComponent"
            toolTip = u"type: TextComponent"
        elif isinstance(widgetLookElement, PyCEGUI.FrameComponent):
            name = u"FrameComponent"
            toolTip = u"type: FrameComponent"

        # Objects that can be owned by a StateImagery:
        elif isinstance(widgetLookElement, PyCEGUI.LayerSpecification):
            name = u"Layer"
            toolTip = u"type: LayerSpecification"

        # Objects that can be owned by a LayerSpecification:
        elif isinstance(widgetLookElement, PyCEGUI.SectionSpecification):
            name = u"Section: \"" + widgetLookElement.getSectionName() + "\""
            if widgetLookElement.getOwnerWidgetLookFeel() != "":
                from ceed.editors.looknfeel.tabbed_editor import LookNFeelTabbedEditor
                originalParts = LookNFeelTabbedEditor.unmapMappedNameIntoOriginalParts(widgetLookElement.getOwnerWidgetLookFeel())
                name += u" look:" + originalParts[0]
            if widgetLookElement.getRenderControlPropertySource() != "":
                name += u" controlProperty:" + widgetLookElement.getRenderControlPropertySource()
            if widgetLookElement.getRenderControlValue() != "":
                name += u" controlValue:" + widgetLookElement.getRenderControlValue()
            toolTip = u"type: SectionSpecification"

        # The ComponentArea element
        elif isinstance(widgetLookElement, PyCEGUI.ComponentArea):
            name = u"Area"
            toolTip = u"type: ComponentArea"

        # The ColourRect element
        elif isinstance(widgetLookElement, PyCEGUI.ColourRect):
            name = u"Colours "
            toolTip = u"type: ColourRect"

        # The Image element
        elif isinstance(widgetLookElement, PyCEGUI.Image):
            name = u"Image (\"" + widgetLookElement.getImage().getName() + u"\")"
            toolTip = u"type: Image"

        return name, toolTip

    def createChildren(self):
        """
        Creates the children items for for the this item's WidgetLookFeel element
        :param:
        :return:
        """
        if isinstance(self.widgetLookElement, PyCEGUI.NamedArea):
            self.createNamedAreaChildren()
        elif isinstance(self.widgetLookElement, PyCEGUI.ImagerySection):
            self.createImagerySectionChildren()
        elif isinstance(self.widgetLookElement, PyCEGUI.StateImagery):
            self.createStateImageryChildren()
        elif isinstance(self.widgetLookElement, PyCEGUI.WidgetComponent):
            self.createWidgetComponentChildren()
        elif isinstance(self.widgetLookElement, PyCEGUI.ImageryComponent):
            self.createImageryComponentChildren()
        elif isinstance(self.widgetLookElement, PyCEGUI.TextComponent):
            self.createTextComponentChildren()
        elif isinstance(self.widgetLookElement, PyCEGUI.FrameComponent):
            self.createFrameComponentChildren()
        elif isinstance(self.widgetLookElement, PyCEGUI.LayerSpecification):
            self.createLayerSpecificationChildren()
        elif isinstance(self.widgetLookElement, PyCEGUI.SectionSpecification):
            self.createSectionSpecificationChildren()

    def createAndAddItem(self, widgetLookElement):
        """
        Creates an item based on the supplied object and adds it to this object
        :param widgetLookElement:
        :return:
        """
        newItem = LookNFeelHierarchyItem(widgetLookElement)
        self.appendRow(newItem)

    def createNamedAreaChildren(self):
        """
        Creates and appends an item for the Area of the NamedArea
        :return:
        """
        area = self.widgetLookElement.getArea()
        self.createAndAddItem(area)

    def createImagerySectionChildren(self):
        """
        Creates and appends children items based on an ImagerySection.
        :return:
        """
        frameCompIter = self.widgetLookElement.getFrameComponentIterator()
        while not frameCompIter.isAtEnd():
            currentFrameComp = frameCompIter.getCurrentValue()
            self.createAndAddItem(currentFrameComp)
            frameCompIter.next()

        textCompIter = self.widgetLookElement.getTextComponentIterator()
        while not textCompIter.isAtEnd():
            currentTextComp = textCompIter.getCurrentValue()
            self.createAndAddItem(currentTextComp)
            textCompIter.next()

        imageryCompIter = self.widgetLookElement.getImageryComponentIterator()
        while not imageryCompIter.isAtEnd():
            imageryComp = imageryCompIter.getCurrentValue()
            self.createAndAddItem(imageryComp)
            imageryCompIter.next()

        coloursRect = self.widgetLookElement.getMasterColours()
        self.createAndAddItem(coloursRect)

    def createStateImageryChildren(self):
        """
        Creates and appends children items based on an ImagerySection.
        :return:
        """
        layerIter = self.widgetLookElement.getLayerIterator()
        while not layerIter.isAtEnd():
            layer = layerIter.getCurrentValue()
            self.createAndAddItem(layer)
            layerIter.next()

    def createWidgetComponentChildren(self):
        """
        Creates and appends children items based on a WidgetComponent (child widget).
        :return:
        """
        area = self.widgetLookElement.getComponentArea()
        self.createAndAddItem(area)

    def createImageryComponentChildren(self):
        """
        Creates and appends children items based on an ImageryComponent.
        :return:
        """
        area = self.widgetLookElement.getComponentArea()
        self.createAndAddItem(area)

    def createTextComponentChildren(self):
        """
        Creates and appends children items based on a TextComponent.
        :return:
        """
        area = self.widgetLookElement.getComponentArea()
        self.createAndAddItem(area)

    def createFrameComponentChildren(self):
        """
        Creates and appends children items based on a FrameComponent.
        :return:
        """
        area = self.widgetLookElement.getComponentArea()
        self.createAndAddItem(area)

        testWindow = PyCEGUI.WindowManager.getSingleton().createWindow("DefaultWindow", "")

        image = self.widgetLookElement.getImage(PyCEGUI.FrameImageComponent.FIC_TOP_LEFT_CORNER, testWindow)
        self.createAndAddItem(image)
        image = self.widgetLookElement.getImage(PyCEGUI.FrameImageComponent.FIC_TOP_RIGHT_CORNER, testWindow)
        self.createAndAddItem(image)
        image = self.widgetLookElement.getImage(PyCEGUI.FrameImageComponent.FIC_BOTTOM_LEFT_CORNER, testWindow)
        self.createAndAddItem(image)
        image = self.widgetLookElement.getImage(PyCEGUI.FrameImageComponent.FIC_BOTTOM_RIGHT_CORNER, testWindow)
        self.createAndAddItem(image)
        image = self.widgetLookElement.getImage(PyCEGUI.FrameImageComponent.FIC_LEFT_EDGE, testWindow)
        self.createAndAddItem(image)
        image = self.widgetLookElement.getImage(PyCEGUI.FrameImageComponent.FIC_RIGHT_EDGE, testWindow)
        self.createAndAddItem(image)
        image = self.widgetLookElement.getImage(PyCEGUI.FrameImageComponent.FIC_TOP_EDGE, testWindow)
        self.createAndAddItem(image)
        image = self.widgetLookElement.getImage(PyCEGUI.FrameImageComponent.FIC_BOTTOM_EDGE, testWindow)
        self.createAndAddItem(image)
        image = self.widgetLookElement.getImage(PyCEGUI.FrameImageComponent.FIC_BACKGROUND, testWindow)
        self.createAndAddItem(image)

        colourRect = self.widgetLookElement.getColours()
        self.createAndAddItem(colourRect)

    def createLayerSpecificationChildren(self):
        """
        Creates and appends children items based on a LayerSpecification.
        :return:
        """
        sectionIter = self.widgetLookElement.getSectionIterator()
        while not sectionIter.isAtEnd():
            currentSectionSpecification = sectionIter.getCurrentValue()
            self.createAndAddItem(currentSectionSpecification)
            sectionIter.next()

    def createSectionSpecificationChildren(self):
        """
        Creates and appends children items based on a SectionSpecification.
        :return:
        """
        colourRect = self.widgetLookElement.getOverrideColours()
        self.createAndAddItem(colourRect)

    def clone(self):
        ret = LookNFeelHierarchyItem(self.manipulator)
        ret.setData(self.data(QtCore.Qt.CheckStateRole), QtCore.Qt.CheckStateRole)
        return ret