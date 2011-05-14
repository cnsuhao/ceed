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

import editors.imageset.elements
import compatibility.imageset

import os
from xml.etree import ElementTree

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
        """Retrieves list of QImage objects each containing a bitmap representation
        of some image this input provided.
        
        For simple images, this will return [QImage(self.path)],
        For imagesets, this will return list of all images in the imageset
        (Each QImage containing only the specified portion of the underlying image)
        """
        
        raise NotImplementedError("Each Input subclass must override Input.getImages!")
    
        return []

class Imageset(Input):
    class FakeImagesetEntry(editors.imageset.elements.ImagesetEntry):
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
        nativeData = compatibility.imageset.Manager.instance.transformTo(compatibility.imageset.EditorNativeType, rawData, self.filePath)
        
        element = ElementTree.fromstring(nativeData)

        self.imagesetEntry = Imageset.FakeImagesetEntry(self.filePath)
        self.imagesetEntry.loadFromElement(element)
    
    def saveToElement(self):
        ret = ElementTree.Element("Imageset")
        ret.set("path", self.path)
    
    def getImages(self):
        assert(self.imagesetEntry is not None)
        
        ret = []
        
        for imageEntry in self.imagesetEntry.imageEntries:
            ret.append(imageEntry.getPixmap().toImage())
        
        return ret
    
class MetaImageset(object):
    def __init__(self, filePath):
        self.filePath = filePath
        
        self.onlyPOT = False
        
        self.output = ""
        self.inputs = []
    
    def loadFromElement(self, element):
        self.output = element.get("output", "")
        
        for imagesetElement in element.findall("Imageset"):
            imageset = Imageset(self)
            imageset.loadFromElement(imagesetElement)
            
            self.inputs.append(imageset)
        
    def saveToElement(self):
        ret = ElementTree.Element("MetaImageset")
        ret.set("output", self.output)
        
        for input in self.inputs:
            element = input.saveToElement()
            ret.append(element)
        
# make compiler visible to the outside
import compiler
