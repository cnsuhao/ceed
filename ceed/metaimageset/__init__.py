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

"""
This module provides all metaimageset API core functionality (except editing)
"""

import ceed.editors.imageset.elements as imageset_elements
import ceed.compatibility.imageset as imageset_compatibility

from PySide import QtGui
from PySide import QtSvg

import os
import glob
from xml.etree import cElementTree as ElementTree
import tempfile
import subprocess

class Image(object):
    """Instance of the image, containing a bitmap (QImage)
    and xoffset and yoffset
    """

    def __init__(self, name, qimage, xoffset = 0, yoffset = 0):
        self.name = name

        self.qimage = qimage

        self.xoffset = xoffset
        self.yoffset = yoffset

class Input(object):
    """Describes any input image source for the meta imageset.

    This can be imageset, bitmap image, SVG image, ...
    """

    def __init__(self, metaImageset):
        """metaImageset - the parent MetaImageset class"""

        self.metaImageset = metaImageset

    def loadFromElement(self, element):
        raise NotImplementedError("Each Input subclass must override Input.loadFromElement!")

    def saveToElement(self):
        raise NotImplementedError("Each Input subclass must override Input.saveToElement!")

    def getImages(self):
        """Retrieves list of Image objects each containing a bitmap representation
        of some image this input provided, xoffset and yoffset.

        For simple images, this will return [ImageInstance(QImage(self.path))],
        For imagesets, this will return list of all images in the imageset
        (Each QImage containing only the specified portion of the underlying image)
        """

        raise NotImplementedError("Each Input subclass must override Input.getImages!")

class Imageset(Input):
    class FakeImagesetEntry(imageset_elements.ImagesetEntry):
        class FakeVisual(object):
            def refreshSceneRect(self):
                pass

        def __init__(self, filePath):
            super(Imageset.FakeImagesetEntry, self).__init__(Imageset.FakeImagesetEntry.FakeVisual())

            self.filePath = filePath

        def getAbsoluteImageFile(self):
            return os.path.join(os.path.dirname(self.filePath), self.imageFile)

    def __init__(self, metaImageset):
        super(Imageset, self).__init__(metaImageset)

        self.filePath = ""
        self.imagesetEntry = None

    def loadFromElement(self, element):
        self.filePath = os.path.join(os.path.dirname(self.metaImageset.filePath), element.get("path", ""))

        rawData = open(self.filePath, "r").read()
        nativeData = imageset_compatibility.manager.transformTo(imageset_compatibility.manager.EditorNativeType, rawData, self.filePath)

        element = ElementTree.fromstring(nativeData)

        self.imagesetEntry = Imageset.FakeImagesetEntry(self.filePath)
        self.imagesetEntry.loadFromElement(element)

    def saveToElement(self):
        ret = ElementTree.Element("Imageset")
        ret.set("path", self.filePath)

        return ret

    def getImages(self):
        assert(self.imagesetEntry is not None)

        ret = []

        for imageEntry in self.imagesetEntry.imageEntries:
            ret.append(Image(self.imagesetEntry.name + "/" + imageEntry.name, imageEntry.getPixmap().toImage(), imageEntry.xoffset, imageEntry.yoffset))

        return ret

class Bitmap(Input):
    def __init__(self, metaImageset):
        super(Bitmap, self).__init__(metaImageset)

        self.path = ""
        self.paths = []

        self.xoffset = 0
        self.yoffset = 0
        self.images = []

    def loadFromElement(self, element):
        self.path = element.get("path", "")
        self.xoffset = int(element.get("xoffset", "0"))
        self.yoffset = int(element.get("yoffset", "0"))

        self.paths = glob.glob(os.path.join(os.path.dirname(self.metaImageset.filePath), self.path))

        for path in self.paths:
            pathSplit = path.rsplit(".", 1)
            name = os.path.basename(pathSplit[0])

            image = Image(name, QtGui.QImage(path), self.xoffset, self.yoffset)
            self.images.append(image)

    def saveToElement(self):
        ret = ElementTree.Element("Bitmap")
        ret.set("path", self.path)
        ret.set("xoffset", str(self.xoffset))
        ret.set("yoffset", str(self.yoffset))

        return ret

    def getImages(self):
        return self.images

class SVG(Input):
    """Simplistic SVGTiny renderer from Qt. This might not interpret effects
    and other features of your SVGs but will be drastically faster and does
    not require Inkscape to be installed.

    It also misses features that might be crucial like exporting components
    from SVG with custom coords and layers.
    """

    def __init__(self, metaImageset):
        super(SVG, self).__init__(metaImageset)

        self.path = ""
        self.paths = []

        self.xoffset = 0
        self.yoffset = 0
        self.images = []

    def loadFromElement(self, element):
        self.path = element.get("path", "")
        self.xoffset = int(element.get("xoffset", "0"))
        self.yoffset = int(element.get("yoffset", "0"))

        self.paths = glob.glob(os.path.join(os.path.dirname(self.metaImageset.filePath), self.path))

        for path in self.paths:
            pathSplit = path.rsplit(".", 1)
            name = os.path.basename(pathSplit[0])

            svgRenderer = QtSvg.QSvgRenderer(path)
            qimage = QtGui.QImage(svgRenderer.defaultSize().width(), svgRenderer.defaultSize().height(), QtGui.QImage.Format_ARGB32)
            qimage.fill(0)
            painter = QtGui.QPainter()
            painter.begin(qimage)
            svgRenderer.render(painter)
            painter.end()

            image = Image(name, qimage, self.xoffset, self.yoffset)
            self.images.append(image)

    def saveToElement(self):
        ret = ElementTree.Element("SVG")
        ret.set("path", self.path)
        ret.set("xoffset", str(self.xoffset))
        ret.set("yoffset", str(self.yoffset))

        return ret

    def getImages(self):
        return self.images

class InkscapeSVG(Input):
    """Just one particular SVGs, support advanced features and renders everything
    using Inkscape, the output should be of higher quality than the SVGTiny renderer
    above. Requires Inkscape to be installed and the inkscape binary to be in $PATH.

    Each component is one "image" to be passed to the metaimageset compiler.
    """

    INKSCAPE_PATH = "inkscape"

    class Component(object):
        def __init__(self, svg):
            self.svg = svg

            self.name = ""

            self.x = 0
            self.y = 0
            self.width = 1
            self.height = 1

            self.layers = []

        @staticmethod
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

        @staticmethod
        def showOnlySVGLayers(svgPath, layers, targetSvg):
            doc = ElementTree.ElementTree(file = svgPath)
            for g in doc.findall(".//{http://www.w3.org/2000/svg}g"):
                if g.get("{http://www.inkscape.org/namespaces/inkscape}groupmode") == "layer":
                    if g.get("{http://www.inkscape.org/namespaces/inkscape}label") in layers:
                        g.set("style", "display:inline")
                    else:
                        g.set("style", "display:none")

            doc.write(targetSvg, encoding = "utf-8")

        @staticmethod
        def exportSVG(svgPath, layers, targetPngPath):
            allLayers = set(InkscapeSVG.Component.getAllSVGLayers(svgPath))
            for layer in layers:
                if not layer in allLayers:
                    raise RuntimeError("Can't export with layer \"%s\", it isn't defined in the SVG \"%s\"!" % (layer, svgPath))

            temporarySvg = tempfile.NamedTemporaryFile(suffix = ".svg")
            InkscapeSVG.Component.showOnlySVGLayers(svgPath, layers, temporarySvg.name)

            cmdLine = [InkscapeSVG.INKSCAPE_PATH, "--file=%s" % (temporarySvg.name), "--export-png=%s" % (targetPngPath)]
            subprocess.call(cmdLine)

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
            InkscapeSVG.Component.exportSVG(self.svg.path, self.layers, temporaryPng.name)

            qimage = QtGui.QImage(temporaryPng.name)
            return qimage.copy(self.x, self.y, self.width, self.height)

        def getImage(self):
            return Image(self.name, self.generateQImage(), self.xoffset, self.yoffset)

    def __init__(self, metaImageset):
        super(InkscapeSVG, self).__init__(metaImageset)

        self.path = ""
        self.components = []

    def loadFromElement(self, element):
        self.path = element.get("path", "")

        for componentElement in element.findall("Component"):
            component = InkscapeSVG.Component(self)
            component.loadFromElement(componentElement)

            self.components.append(component)

    def saveToElement(self):
        ret = ElementTree.Element("InkscapeSVG")
        ret.set("path", self.path)

        for component in self.components:
            ret.append(component.saveToElement())

        return ret

    def getImages(self):
        return [component.getImage() for component in self.components]

class MetaImageset(object):
    def __init__(self, filePath):
        self.filePath = filePath

        self.name = ""
        self.nativeHorzRes = 800
        self.nativeVertRes = 600
        self.autoScaled = False

        self.onlyPOT = False

        self.output = ""
        self.outputTargetType = imageset_compatibility.manager.EditorNativeType
        self.inputs = []

    def getOutputDirectory(self):
        return os.path.abspath(os.path.dirname(self.filePath))

    def loadFromElement(self, element):
        self.name = element.get("name", "")
        self.nativeHorzRes = int(element.get("nativeHorzRes", "800"))
        self.nativeVertRes = int(element.get("nativeVertRes", "600"))
        self.autoScaled = element.get("autoScaled", "false") == "true"

        self.outputTargetType = element.get("outputTargetType", imageset_compatibility.manager.EditorNativeType)
        self.output = element.get("output", "")

        for childElement in element.findall("Imageset"):
            imageset = Imageset(self)
            imageset.loadFromElement(childElement)

            self.inputs.append(imageset)

        for childElement in element.findall("Bitmap"):
            bitmap = Bitmap(self)
            bitmap.loadFromElement(childElement)

            self.inputs.append(bitmap)

        for childElement in element.findall("SVG"):
            svg = SVG(self)
            svg.loadFromElement(childElement)

            self.inputs.append(svg)

        for childElement in element.findall("InkscapeSVG"):
            svg = InkscapeSVG(self)
            svg.loadFromElement(childElement)

            self.inputs.append(svg)

    def saveToElement(self):
        ret = ElementTree.Element("MetaImageset")
        ret.set("name", self.name)
        ret.set("nativeHorzRes", str(self.nativeHorzRes))
        ret.set("nativeVertRes", str(self.nativeVertRes))
        ret.set("autoScaled", "true" if self.autoScaled else "false")

        ret.set("outputTargetType", self.outputTargetType)
        ret.set("output", self.output)

        for input_ in self.inputs:
            element = input_.saveToElement()
            ret.append(element)

        return ret
