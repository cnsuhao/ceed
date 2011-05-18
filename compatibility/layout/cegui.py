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

CEGUILayout2 = "CEGUI layout 2"
CEGUILayout3 = "CEGUI layout 3"
CEGUILayout4 = "CEGUI layout 4"

class Layout2TypeDetector(compatibility.TypeDetector):
    def getType(self):
        return CEGUILayout2
    
    def getPossibleExtensions(self):
        return ["layout"]
    
    def matches(self, data, extension):
        if extension not in ["", "layout"]:
            return False
        
        # todo: we should be at least a bit more precise
        # (implement XSD based TypeDetector?)
        
        try:
            root = ElementTree.fromstring(data)
            if root.tag != "GUILayout":
                return False
            
            # Layout 2 has no version indication :-(
            return True
        
        except:
            return False

class Layout3TypeDetector(compatibility.TypeDetector):
    def getType(self):
        return CEGUILayout3
    
    def getPossibleExtensions(self):
        return ["layout"]
    
    def matches(self, data, extension):
        if extension not in ["", "layout"]:
            return False
        
        # todo: we should be at least a bit more precise
        # (implement XSD based TypeDetector?)
        
        try:
            root = ElementTree.fromstring(data)
            if root.tag != "GUILayout":
                return False
            
            # Layout 3 has no version indication :-(
            return True
        
        except:
            return False

class Layout4TypeDetector(compatibility.TypeDetector):
    def getType(self):
        return CEGUILayout4
    
    def getPossibleExtensions(self):
        return ["layout"]
    
    def matches(self, data, extension):
        if extension not in ["", "layout"]:
            return False
        
        # todo: we should be at least a bit more precise
        # (implement XSD based TypeDetector?)
        
        try:
            root = ElementTree.fromstring(data)
            if root.tag != "GUILayout":
                return False
            
            # TODO: Layout 4 has no version indication yet :-(
            return True
        
        except:
            return False
        
class Layout3To4Layer(compatibility.Layer):
    def getSourceType(self):
        return CEGUILayout3
    
    def getTargetType(self):
        return CEGUILayout4
    
    def convertToRelativeNames(self, window, leadingName = ""):
        ret = ""
        
        name = window.get("Name", "")
    
        if name.startswith(leadingName + "/"):
            name = name[len(leadingName + "/"):]
            
            for childWindow in window.findall("Window"):
                ret += self.convertToRelativeNames(childWindow, leadingName + "/" + name)
        else:
            
            for childWindow in window.findall("Window"):
                ret += self.convertToRelativeNames(childWindow, name)
        
        delimiterPosition = name.rfind("/")        
        if delimiterPosition != -1:
            oldName = name
            name = name[delimiterPosition + 1:]
            
            ret += "Warning: Renaming '%s' to '%s' because it contains '/' even after prefix stripping (and '/' is a disallowed character!)\n" % (oldName, name)
    
        window.set("Name", name)
        
        return ret
    
    def convertAutoWindowSuffix(self, autoWindow):
        autoWindow.set("NamePath", autoWindow.get("NameSuffix"))
        del autoWindow.attrib["NameSuffix"]
    
        for childAutoWindow in autoWindow.findall("AutoWindow"):
            self.convertAutoWindowSuffix(childAutoWindow)
    
    def applyChangesRecursively(self, window):
        ret = ""
        
        # convert the properties that had 'Unified' prefix
        for property in window.findall("Property"):
            name = property.get("Name", "")
            
            if name == "UnifiedAreaRect":
                name = "Area"
            elif name == "UnifiedPosition":
                name = "Position"
            elif name == "UnifiedXPosition":
                name = "XPosition"
            elif name == "UnifiedYPosition":
                name = "YPosition"
            elif name == "UnifiedSize":
                name = "Size"
            elif name == "UnifiedWidth":
                name = "Width"
            elif name == "UnifiedHeight":
                name = "Height"
            elif name == "UnifiedMinSize":
                name = "MinSize"
            elif name == "UnifiedMaxSize":
                name = "MaxSize"
            
            if name != "":
                property.set("Name", name)
        
        # convert NameSuffix to NamePath
        for autoWindow in window.findall("AutoWindow"):
            self.convertAutoWindowSuffix(autoWindow)
        
        for childWindow in window.findall("Window"):
            self.applyChangesRecursively(childWindow)
            
        #window.tag = "Widget"
        
        return ret
    
    def transform(self, data):
        log = ""
        
        root = ElementTree.fromstring(data)
        
        for window in root.findall("Window"):
            # should be only one window
            
            # first make the names relative to parent
            log += self.convertToRelativeNames(window)
            
            # apply other changes
            log += self.applyChangesRecursively(window)
            
        return ElementTree.tostring(root, "utf-8")

class Layout4To3Layer(compatibility.Layer):
    def getSourceType(self):
        return CEGUILayout4
    
    def getTargetType(self):
        return CEGUILayout3
    
    def convertToAbsoluteNames(self, window, leadingName = ""):
        ret = ""
        
        name = window.get("Name", "")
        if leadingName != "":
            name = leadingName + "/" + name
        
        for childWindow in window.findall("Window"):
            ret += self.convertToAbsoluteNames(childWindow, name)
    
        window.set("Name", name)
        
        return ret
    
    def convertAutoWindowSuffix(self, autoWindow):
        autoWindow.set("NameSuffix", autoWindow.get("NamePath"))
        del autoWindow.attrib["NamePath"]
    
        for childAutoWindow in autoWindow.findall("AutoWindow"):
            self.convertAutoWindowSuffix(childAutoWindow)
    
    def applyChangesRecursively(self, window):
        ret = ""
        
        # convert the properties that had 'Unified' prefix in 0.7
        for property in window.findall("Property"):
            name = property.get("Name", "")
            
            if name == "Area":
                name = "UnifiedAreaRect"
            elif name == "Position":
                name = "UnifiedPosition"
            elif name == "XPosition":
                name = "UnifiedXPosition"
            elif name == "YPosition":
                name = "UnifiedYPosition"
            elif name == "Size":
                name = "UnifiedSize"
            elif name == "Width":
                name = "UnifiedWidth"
            elif name == "Height":
                name = "UnifiedHeight"
            elif name == "MinSize":
                name = "UnifiedMinSize"
            elif name == "MaxSize":
                name = "UnifiedMaxSize"
            
            if name != "":
                property.set("Name", name)
        
        # convert NameSuffix to NamePath
        for autoWindow in window.findall("AutoWindow"):
            self.convertAutoWindowSuffix(autoWindow)
        
        for childWindow in window.findall("Window"):
            self.applyChangesRecursively(childWindow)
        
        return ret
    
    def transform(self, data):
        log = ""
        
        root = ElementTree.fromstring(data)
        
        for window in root.findall("Window"):
            # should be only one window
            
            # first make the names relative to parent
            log += self.convertToAbsoluteNames(window)
            
            # apply other changes
            log += self.applyChangesRecursively(window)
            
        return ElementTree.tostring(root, "utf-8")
