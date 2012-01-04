################################################################################
#   CEED - A unified CEGUI editor
#   Copyright (C) 2011 Martin Preisler <preisler.m@gmail.com>
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
################################################################################

# This module provides all metaimageset API core functionality (except editing)

import ceed.editors.imageset.elements as imageset_elements
import ceed.compatibility.imageset as imageset_compatibility

from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtSvg import *

import os
from xml.etree import ElementTree

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
    
    def saveToElement(self, element):
        raise NotImplementedError("Each Input subclass must override Input.saveToElement!")
    
    def getImages(self):
        """Retrieves list of Image objects each containing a bitmap representation
        of some image this input provided, xoffset and yoffset.
        
        For simple images, this will return [ImageInstance(QImage(self.path))],
        For imagesets, this will return list of all images in the imageset
        (Each QImage containing only the specified portion of the underlying image)
        """
        
        raise NotImplementedError("Each Input subclass must override Input.getImages!")
    
        return []

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
        
        self.imagesetEntry = None
    
    def loadFromElement(self, element):
        self.filePath = os.path.join(os.path.dirname(self.metaImageset.filePath), element.get("path", ""))
        
        rawData = open(self.filePath, "r").read()
        nativeData = imageset_compatibility.Manager.instance.transformTo(imageset_compatibility.Manager.instance.EditorNativeType, rawData, self.filePath)
        
        element = ElementTree.fromstring(nativeData)

        self.imagesetEntry = Imageset.FakeImagesetEntry(self.filePath)
        self.imagesetEntry.loadFromElement(element)
    
    def saveToElement(self):
        ret = ElementTree.Element("Imageset")
        ret.set("path", self.filePath)
    
    def getImages(self):
        assert(self.imagesetEntry is not None)
        
        ret = []
        
        for imageEntry in self.imagesetEntry.imageEntries:
            ret.append(Image(self.imagesetEntry.name + "/" + imageEntry.name, imageEntry.getPixmap().toImage(), imageEntry.xoffset, imageEntry.yoffset))
        
        return ret
    
class Bitmap(Input):
    def __init__(self, metaImageset):
        super(Bitmap, self).__init__(metaImageset)
        
        self.xoffset = 0
        self.yoffset = 0
        self.images = []
    
    def loadFromElement(self, element):
        self.path = element.get("path", "")
        self.xoffset = int(element.get("xoffset", "0"))
        self.yoffset = int(element.get("yoffset", "0"))
        
        import glob
        self.paths = glob.glob(os.path.join(os.path.dirname(self.metaImageset.filePath), self.path))

        for path in self.paths:
            pathSplit = path.rsplit(".", 1)
            name = os.path.basename(pathSplit[0])
            
            image = Image(name, QImage(path), self.xoffset, self.yoffset)
            self.images.append(image)
    
    def saveToElement(self):
        ret = ElementTree.Element("Bitmap")
        ret.set("path", self.path)
        ret.set("xoffset", str(self.xoffset))
        ret.set("yoffset", str(self.yoffset))
    
    def getImages(self):
        return self.images

class SVG(Input):
    def __init__(self, metaImageset):
        super(SVG, self).__init__(metaImageset)
        
        self.xoffset = 0
        self.yoffset = 0
        self.images = []
    
    def loadFromElement(self, element):
        self.path = element.get("path", "")
        self.xoffset = int(element.get("xoffset", "0"))
        self.yoffset = int(element.get("yoffset", "0"))
        
        import glob
        self.paths = glob.glob(os.path.join(os.path.dirname(self.metaImageset.filePath), self.path))

        for path in self.paths:
            pathSplit = path.rsplit(".", 1)
            name = os.path.basename(pathSplit[0])
            
            svgRenderer = QSvgRenderer(path)
            qimage = QImage(svgRenderer.defaultSize().width(), svgRenderer.defaultSize().height(), QImage.Format_ARGB32)
            qimage.fill(0)
            painter = QPainter()
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
    
    def getImages(self):
        return self.images

class MetaImageset(object):
    def __init__(self, filePath):
        self.filePath = filePath
        
        self.name = ""
        self.nativeHorzRes = 800
        self.nativeVertRes = 600
        self.autoScaled = False
        
        self.onlyPOT = False
        
        self.output = ""
        self.outputTargetType = imageset_compatibility.Manager.instance.EditorNativeType
        self.inputs = []
    
    def getOutputDirectory(self):
        return os.path.abspath(os.path.dirname(self.filePath))
    
    def loadFromElement(self, element):
        self.name = element.get("name", "")
        self.nativeHorzRes = int(element.get("nativeHorzRes", "800"))
        self.nativeVertRes = int(element.get("nativeVertRes", "600"))
        self.autoScaled = element.get("autoScaled", "false") == "true"
        
        self.outputTargetType = element.get("outputTargetType", imageset_compatibility.Manager.instance.EditorNativeType)
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
        
    def saveToElement(self):
        ret = ElementTree.Element("MetaImageset")
        ret.set("name", self.name)
        ret.set("nativeHorzRes", str(self.nativeHorzRes))
        ret.set("nativeVertRes", str(self.nativeVertRes))
        ret.set("autoScaled", "true" if self.autoScaled else "false")
        
        ret.set("outputTargetType", self.outputTargetType)
        ret.set("output", self.output)
        
        for input in self.inputs:
            element = input.saveToElement()
            ret.append(element)
