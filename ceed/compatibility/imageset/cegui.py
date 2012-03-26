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

CEGUIImageset1 = "CEGUI imageset 1"
CEGUIImageset2 = "CEGUI imageset 2"

class Imageset1TypeDetector(compatibility.TypeDetector):
    def getType(self):
        return CEGUIImageset1
    
    def getPossibleExtensions(self):
        return {"imageset"}
    
    def matches(self, data, extension):
        if extension not in ["", "imageset"]:
            return False
        
        try:
            root = ElementTree.fromstring(data)
            if root.tag != "Imageset":
                return False
            
            # Imageset1 has no version indication :-(
            # However if there is a version attribute, we can be sure it's not Imageset1
            if root.get("version") is not None:
                return False
            
            return True
        
        except:
            return False
        
        # todo: we should be at least a bit more precise
        # (implement XSD based TypeDetector?)
        return True

class Imageset2TypeDetector(compatibility.TypeDetector):
    def getType(self):
        return CEGUIImageset2
    
    def getPossibleExtensions(self):
        return {"imageset"}
    
    def matches(self, data, extension):
        if extension not in ["", "imageset"]:
            return False
        
        try:
            root = ElementTree.fromstring(data)
            if root.tag != "Imageset":
                return False
            
            if root.get("version", "unknown") != "2":
                return False
            
            return True
        
        except:
            return False
        
        return True

class CEGUI1ToCEGUI2Layer(compatibility.Layer):
    def getSourceType(self):
        return CEGUIImageset1
    
    def getTargetType(self):
        return CEGUIImageset2
    
    def transform(self, data):
        root = ElementTree.fromstring(data)
        root.set("version", "2")
        
        root.set("name", root.get("Name", ""))
        del root.attrib["Name"]
        
        root.set("imagefile", root.get("Imagefile", ""))
        del root.attrib["Imagefile"]
        
        if root.get("NativeHorzRes") is not None:
            root.set("nativeHorzRes", root.get("NativeHorzRes", "640"))
            del root.attrib["NativeHorzRes"]
        
        if root.get("NativeVertRes") is not None:
            root.set("nativeVertRes", root.get("NativeVertRes", "480"))
            del root.attrib["NativeVertRes"]
        
        root.set("autoScaled", root.get("AutoScaled", "false"))
        del root.attrib["AutoScaled"]
        
        for image in root.findall("Image"):
            image.set("name", image.get("Name", ""))
            del image.attrib["Name"]
            
            image.set("xPos", image.get("XPos", "0"))
            del image.attrib["XPos"]
            
            image.set("yPos", image.get("YPos", "0"))
            del image.attrib["YPos"]
            
            image.set("width", image.get("Width", "1"))
            del image.attrib["Width"]
            
            image.set("height", image.get("Height", "1"))
            del image.attrib["Height"]
            
            if image.get("XOffset") is not None:
                image.set("xOffset", image.get("XOffset", "0"))
                del image.attrib["xOffset"]
                
            if image.get("YOffset") is not None:
                image.set("yOffset", image.get("YOffset", "0"))
                del image.attrib["yOffset"]

        return ElementTree.tostring(root, "utf-8")

class CEGUI2ToCEGUI1Layer(compatibility.Layer):
    def getSourceType(self):
        return CEGUIImageset2
    
    def getTargetType(self):
        return CEGUIImageset1
    
    def transform(self, data):
        root = ElementTree.fromstring(data)
        del root.attrib["version"] # imageset version 1 has no version attribute!
        
        root.set("Name", root.get("name", ""))
        del root.attrib["name"]
        
        root.set("Imagefile", root.get("imagefile", ""))
        del root.attrib["imagefile"]
        
        if root.get("nativeHorzRes") is not None:
            root.set("NativeHorzRes", root.get("nativeHorzRes", "640"))
            del root.attrib["nativeHorzRes"]
        
        if root.get("nativeVertRes") is not None:
            root.set("NativeVertRes", root.get("nativeVertRes", "480"))
            del root.attrib["nativeVertRes"]
        
        root.set("AutoScaled", root.get("autoScaled", "false"))
        del root.attrib["autoScaled"]
        
        for image in root.findall("Image"):
            image.set("Name", image.get("name", ""))
            del image.attrib["name"]
            
            image.set("XPos", image.get("xPos", "0"))
            del image.attrib["xPos"]
            
            image.set("YPos", image.get("yPos", "0"))
            del image.attrib["yPos"]
            
            image.set("Width", image.get("width", "1"))
            del image.attrib["width"]
            
            image.set("Height", image.get("height", "1"))
            del image.attrib["height"]
            
            if image.get("xOffset") is not None:
                image.set("XOffset", image.get("xOffset", "0"))
                del image.attrib["XOffset"]
                
            if image.get("yOffset") is not None:
                image.set("YOffset", image.get("yOffset", "0"))
                del image.attrib["YOffset"]

        return ElementTree.tostring(root, "utf-8")
