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

import compatibility
from xml.etree import ElementTree

CEGUILookNFeel1 = "CEGUI LookNFeel 1"
# superseded by LookNFeel 2 in 0.5b
#CEGUILookNFeel2 = "CEGUI LookNFeel 2"
CEGUILookNFeel3 = "CEGUI LookNFeel 3"
CEGUILookNFeel4 = "CEGUI LookNFeel 4"
# superseded by LookNFeel 6 in 0.7
#CEGUILookNFeel5 = "CEGUI LookNFeel 5"
CEGUILookNFeel6 = "CEGUI LookNFeel 6"
CEGUILookNFeel7 = "CEGUI LookNFeel 7"

class LookNFeel6TypeDetector(compatibility.TypeDetector):
    def getType(self):
        return CEGUILookNFeel6
    
    def getPossibleExtensions(self):
        return ["looknfeel"]
    
    def matches(self, data, extension):
        if extension not in ["", "looknfeel"]:
            return False
        
        # todo: we should be at least a bit more precise
        # (implement XSD based TypeDetector?)
        
        try:
            root = ElementTree.fromstring(data)
            if root.tag != "Falagard":
                return False
            
            # version 6 doesn't have any version tag! so if there is a version tag (of any value) it can't be version 6
            if root.get("version") is not None:
                return False

            return True
        
        except:
            return False

class LookNFeel7TypeDetector(compatibility.TypeDetector):
    def getType(self):
        return CEGUILookNFeel7
    
    def getPossibleExtensions(self):
        return ["looknfeel"]
    
    def matches(self, data, extension):
        if extension not in ["", "looknfeel"]:
            return False
        
        # todo: we should be at least a bit more precise
        # (implement XSD based TypeDetector?)
        
        try:
            root = ElementTree.fromstring(data)
            if root.tag != "Falagard":
                return False
            
            if root.get("version", "unknown") != "7":
                return False

            return True
        
        except:
            return False

class LookNFeel6To7Layer(compatibility.Layer):
    def getSourceType(self):
        return CEGUILookNFeel6
    
    def getTargetType(self):
        return CEGUILookNFeel7
    
    def transform(self, data):
        log = ""
        
        root = ElementTree.fromstring(data)
        
        # version 7 has a version attribute
        root.set("version", "7")
        
        # TODO: set:Imageset image:Image -> Imageset/Image
        # TODO: Carat -> Caret
            
        return ElementTree.tostring(root, "utf-8")


class LookNFeel7To6Layer(compatibility.Layer):
    def getSourceType(self):
        return CEGUILookNFeel7
    
    def getTargetType(self):
        return CEGUILookNFeel6
    
    def transform(self, data):
        log = ""
        
        root = ElementTree.fromstring(data)
        
        # version 6 must not have a version attribute
        del root.attrib["version"]
        
        # TODO: set:Imageset image:Image <- Imageset/Image
        # TODO: Carat <- Caret
            
        return ElementTree.tostring(root, "utf-8")
