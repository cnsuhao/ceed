##############################################################################
#   CEED - Unified CEGUI asset editor
#
#   Copyright (C) 2011-2012   Martin Preisler <martin@preisler.me>
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

"""Implements the more advanced SVG input of metaimageset (using Inkscape).
"""

from ceed.metaimageset import inputs

from PySide import QtGui

import os.path
from xml.etree import cElementTree as ElementTree
import tempfile
import subprocess

INKSCAPE_PATH = "inkscape"

def getAllSVGLayers(svgPath):
    """Retrieves all Inkscape layers defined in given SVG.

    Note: I couldn't figure out how to do this with inkscape CLI
    """

    ret = []

    doc = ElementTree.ElementTree(file = svgPath)
    for g in doc.findall(".//{http://www.w3.org/2000/svg}g"):
        if g.get("{http://www.inkscape.org/namespaces/inkscape}groupmode") == "layer":
            ret.append(g.get("{http://www.inkscape.org/namespaces/inkscape}label"))

    return ret

def showOnlySVGLayers(svgPath, layers, targetSvg):
    doc = ElementTree.ElementTree(file = svgPath)
    for g in doc.findall(".//{http://www.w3.org/2000/svg}g"):
        if g.get("{http://www.inkscape.org/namespaces/inkscape}groupmode") == "layer":
            if g.get("{http://www.inkscape.org/namespaces/inkscape}label") in layers:
                g.set("style", "display:inline")
            else:
                g.set("style", "display:none")

    doc.write(targetSvg, encoding = "utf-8")

def exportSVG(svgPath, layers, targetPngPath):
    allLayers = set(getAllSVGLayers(svgPath))
    for layer in layers:
        if not layer in allLayers:
            raise RuntimeError("Can't export with layer \"%s\", it isn't defined in the SVG \"%s\"!" % (layer, svgPath))

    temporarySvg = tempfile.NamedTemporaryFile(suffix = ".svg")
    showOnlySVGLayers(svgPath, layers, temporarySvg.name)

    cmdLine = [INKSCAPE_PATH, "--file=%s" % (temporarySvg.name), "--export-png=%s" % (targetPngPath)]
    subprocess.call(cmdLine)

class Component(object):
    def __init__(self, svg, name = "", x = 0, y = 0, width = 1, height = 1, layers = "", xoffset = 0, yoffset = 0):
        self.svg = svg

        self.name = name

        self.x = x
        self.y = y
        self.width = width
        self.height = height

        self.xoffset = xoffset
        self.yoffset = yoffset

        self.layers = layers.split(" ")

        self.cachedImage = None

    def loadFromElement(self, element):
        self.name = element.get("name", "")

        self.x = int(element.get("x", "0"))
        self.y = int(element.get("y", "0"))
        self.width = int(element.get("width", "1"))
        self.height = int(element.get("height", "1"))

        self.xoffset = int(element.get("xoffset", "0"))
        self.yoffset = int(element.get("yoffset", "0"))

        self.layers = element.get("layers", "").split(" ")

    def saveToElement(self):
        ret = ElementTree.Element("Component")

        ret.set("name", self.name)
        ret.set("x", str(self.x))
        ret.set("y", str(self.y))
        ret.set("width", str(self.width))
        ret.set("height", str(self.height))

        ret.set("xoffset", str(self.xoffset))
        ret.set("yoffset", str(self.yoffset))

        ret.set("layers", " ".join(self.layers))

        return ret

    def generateQImage(self):
        temporaryPng = tempfile.NamedTemporaryFile(suffix = ".png")
        exportSVG(self.svg.path, self.layers, temporaryPng.name)

        qimage = QtGui.QImage(temporaryPng.name)
        return qimage.copy(self.x, self.y, self.width, self.height)

    def getImage(self):
        # FIXME: This is a really nasty optimisation, it can be done way better
        #        but would probably require a slight redesign of inputs.Input
        if self.cachedImage is None:
            self.cachedImage = inputs.Image(self.name, self.generateQImage(), self.xoffset, self.yoffset)

        return self.cachedImage

class InkscapeSVG(inputs.Input):
    """Just one particular SVGs, support advanced features and renders everything
    using Inkscape, the output should be of higher quality than the SVGTiny renderer
    above. Requires Inkscape to be installed and the inkscape binary to be in $PATH.

    Each component is one "image" to be passed to the metaimageset compiler.
    """

    def __init__(self, metaImageset):
        super(InkscapeSVG, self).__init__(metaImageset)

        self.path = ""
        self.components = []

    def loadFromElement(self, element):
        self.path = element.get("path", "")

        for componentElement in element.findall("Component"):
            component = Component(self)
            component.loadFromElement(componentElement)

            self.components.append(component)

        # FrameComponent is a shortcut to avoid having to type out 9 components
        for componentElement in element.findall("FrameComponent"):
            # TODO: This doesn't save the same way it loads!

            # Doing processing in the parsing stage may be evil
            # but we do it anyways!

            name = componentElement.get("name", "")

            x = int(componentElement.get("x", "0"))
            y = int(componentElement.get("y", "0"))
            width = int(componentElement.get("width", "1"))
            height = int(componentElement.get("height", "1"))
            cornerWidth = int(componentElement.get("cornerWidth", "1"))
            cornerHeight = int(componentElement.get("cornerHeight", "1"))
            layers = componentElement.get("layers", "")

            # This allows the user to tell us to skip particular images of
            # the frame. This is useful when the fill in the middle is split
            # for example.
            skip = componentElement.get("skip", "").split(" ")

            if "centre" not in skip:
                centre = Component(self, "%sCentre" % (name), x + cornerWidth, y + cornerHeight, width - 2 * cornerWidth, height - 2 * cornerHeight, layers)
                self.components.append(centre)

            if "top" not in skip:
                top = Component(self, "%sTop" % (name), x + cornerWidth, y, width - 2 * cornerWidth, cornerHeight, layers)
                self.components.append(top)

            if "bottom" not in skip:
                bottom = Component(self, "%sBottom" % (name), x + cornerWidth, y + height - cornerHeight, width - 2 * cornerWidth, cornerHeight, layers)
                self.components.append(bottom)

            if "left" not in skip:
                left = Component(self, "%sLeft" % (name), x, y + cornerHeight, cornerWidth, height - 2 * cornerHeight, layers)
                self.components.append(left)

            if "right" not in skip:
                right = Component(self, "%sRight" % (name), x + width - cornerWidth, y + cornerHeight, cornerWidth, height - 2 * cornerHeight, layers)
                self.components.append(right)

            if "topLeft" not in skip:
                topLeft = Component(self, "%sTopLeft" % (name), x, y, cornerWidth, cornerHeight, layers)
                self.components.append(topLeft)

            if "topRight" not in skip:
                topRight = Component(self, "%sTopRight" % (name), x + width - cornerWidth, y, cornerWidth, cornerHeight, layers)
                self.components.append(topRight)

            if "bottomLeft" not in skip:
                bottomLeft = Component(self, "%sBottomLeft" % (name), x, y + height - cornerHeight, cornerWidth, cornerHeight, layers)
                self.components.append(bottomLeft)

            if "bottomRight" not in skip:
                bottomRight = Component(self, "%sBottomRight" % (name), x + width - cornerWidth, y + height - cornerHeight, cornerWidth, cornerHeight, layers)
                self.components.append(bottomRight)

    def saveToElement(self):
        ret = ElementTree.Element("InkscapeSVG")
        ret.set("path", self.path)

        for component in self.components:
            ret.append(component.saveToElement())

        return ret

    def getImages(self):
        return [component.getImage() for component in self.components]
