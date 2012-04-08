##############################################################################
#   CEED - Unified CEGUI asset editor
#
#   Copyright (C) 2011-2012   Martin Preisler <preisler.m@gmail.com>
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

from ceed import compatibility
from xml.etree import ElementTree

CEGUIScheme1 = "CEGUI Scheme 1"
CEGUIScheme2 = "CEGUI Scheme 2"
CEGUIScheme3 = "CEGUI Scheme 3"
CEGUIScheme4 = "CEGUI Scheme 4"
CEGUIScheme5 = "CEGUI Scheme 5"

class Scheme4TypeDetector(compatibility.TypeDetector):
    def getType(self):
        return CEGUIScheme4
    
    def getPossibleExtensions(self):
        return {"scheme"}
    
    def matches(self, data, extension):
        if extension not in ["", "scheme"]:
            return False
        
        try:
            root = ElementTree.fromstring(data)
            
            if root.tag != "GUIScheme":
                return False
            
            # GUIScheme4 has no version indication :-(
            # However if there is a version attribute, we can be sure it's not GUIScheme4
            if root.get("version") is not None:
                return False
            
            return True
        
        except:
            return False
        
        # todo: we should be at least a bit more precise
        # (implement XSD based TypeDetector?)
        return True
    
class Scheme5TypeDetector(compatibility.TypeDetector):
    def getType(self):
        return CEGUIScheme5
    
    def getPossibleExtensions(self):
        return {"scheme"}
    
    def matches(self, data, extension):
        if extension not in ["", "scheme"]:
            return False
        
        try:
            root = ElementTree.fromstring(data)
            if root.tag != "GUIScheme":
                return False
            
            if root.get("version", "unknown") != "5":
                return False
            
            return True
        
        except:
            return False
        
        return True
        
        # todo: we should be at least a bit more precise
        # (implement XSD based TypeDetector?)
        return True


class CEGUI4ToCEGUI5Layer(compatibility.Layer):
    def getSourceType(self):
        return CEGUIScheme4
    
    def getTargetType(self):
        return CEGUIScheme5
    
    def transformAttribute(self, element, attribute):
        sourceAttributeName = attribute[0].upper() + attribute[1:]
        targetAttributeName = sourceAttributeName[0].lower() + sourceAttributeName[1:]
        
        if element.get(sourceAttributeName) is not None:
            element.set(targetAttributeName, element.get(sourceAttributeName))
            del element.attrib[sourceAttributeName]
    
    def transformNamedType(self, element):
        self.transformAttribute(element, "name")
        self.transformAttribute(element, "filename")
        self.transformAttribute(element, "resourceGroup")
    
    def transform(self, data):
        root = ElementTree.fromstring(data)
        root.set("version", "5")
        
        self.transformAttribute(root, "name")
            
        for imageset in root.findall("Imageset"):
            self.transformNamedType(imageset)
        for imagesetFromFile in root.findall("ImagesetFromFile"):
            self.transformNamedType(imagesetFromFile)
        for font in root.findall("Font"):
            self.transformNamedType(font)
        for looknfeel in root.findall("LookNFeel"):
            self.transformNamedType(looknfeel)
        
        for windowSet in root.findall("WindowSet"):
            self.transformAttribute(windowRendererSet, "filename")
            
            for windowFactory in windowSet.findall("WindowFactory"):
                self.transformAttribute(windowFactory, "name")
        
        for windowRendererSet in root.findall("WindowRendererSet"):
            self.transformAttribute(windowRendererSet, "filename")
            
            # this particular window renderer set got renamed
            if windowRendererSet.get("filename", "") == "CEGUIFalagardWRBase":
                windowRendererSet.set("filename", "CEGUICoreWindowRendererSet")
                
            for windowRendererFactory in windowRendererSet.findall("WindowRendererFactory"):
                self.transformAttribute(windowRendererFactory, "name")

        for windowAlias in root.findall("WindowAlias"):
            self.transformAttribute(windowAlias, "alias")
            self.transformAttribute(windowAlias, "target")

        for falagardMapping in root.findall("FalagardMapping"):
            for attr in ["windowType", "targetType", "renderer", "lookNFeel", "renderEffect"]:
                self.transformAttribute(falagardMapping, attr)

            if falagardMapping.get("renderer") is not None:
                rendererValue = falagardMapping.get("renderer")
                if rendererValue.startswith("Falagard/"):
                    falagardMapping.set("renderer", "Core/%s" % (rendererValue[9:]))

        return ElementTree.tostring(root, "utf-8")

class CEGUI5ToCEGUI4Layer(compatibility.Layer):
    def getSourceType(self):
        return CEGUIScheme5
    
    def getTargetType(self):
        return CEGUIScheme4
    
    def transformAttribute(self, element, attribute):
        targetAttributeName = attribute[0].upper() + attribute[1:]
        sourceAttributeName = targetAttributeName[0].lower() + targetAttributeName[1:]
        
        if element.get(sourceAttributeName) is not None:
            element.set(targetAttributeName, element.get(sourceAttributeName))
            del element.attrib[sourceAttributeName]
    
    def transformNamedType(self, element):
        self.transformAttribute(element, "name")
        self.transformAttribute(element, "filename")
        self.transformAttribute(element, "resourceGroup")
    
    def transform(self, data):
        root = ElementTree.fromstring(data)
        del root.attrib["version"]
              
        self.transformAttribute(root, "name")
        
        for imageset in root.findall("Imageset"):
            self.transformNamedType(imageset)
        for imagesetFromFile in root.findall("ImagesetFromFile"):
            self.transformNamedType(imagesetFromFile)
        for font in root.findall("Font"):
            self.transformNamedType(font)
        for looknfeel in root.findall("LookNFeel"):
            self.transformNamedType(looknfeel)
        
        for windowSet in root.findall("WindowSet"):
            self.transformAttribute(windowRendererSet, "filename")
            
            for windowFactory in windowSet.findall("WindowFactory"):
                self.transformAttribute(windowFactory, "name")
        
        for windowRendererSet in root.findall("WindowRendererSet"):
            self.transformAttribute(windowRendererSet, "filename")
            
            # this particular window renderer set got renamed
            if windowRendererSet.get("Filename", "") == "CEGUICoreWindowRendererSet":
                windowRendererSet.set("Filename", "CEGUIFalagardWRBase")
                
            for windowRendererFactory in windowRendererSet.findall("WindowRendererFactory"):
                self.transformAttribute(windowRendererFactory, "name")

        for windowAlias in root.findall("WindowAlias"):
            self.transformAttribute(windowAlias, "alias")
            self.transformAttribute(windowAlias, "target")

        for falagardMapping in root.findall("FalagardMapping"):
            for attr in ["windowType", "targetType", "renderer", "lookNFeel", "renderEffect"]:
                self.transformAttribute(falagardMapping, attr)

            if falagardMapping.get("Renderer") is not None:
                rendererValue = falagardMapping.get("Renderer")
                if rendererValue.startswith("Core/"):
                    falagardMapping.set("Renderer", "Falagard/%s" % (rendererValue[5:]))

        return ElementTree.tostring(root, "utf-8")
