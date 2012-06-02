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
from xml.etree import cElementTree as ElementTree

CEGUILayout2 = "CEGUI layout 2"
CEGUILayout3 = "CEGUI layout 3"
CEGUILayout4 = "CEGUI layout 4"

class Layout2TypeDetector(compatibility.TypeDetector):
    def getType(self):
        return CEGUILayout2
    
    def getPossibleExtensions(self):
        return set(["layout"])
    
    def matches(self, data, extension):
        if extension not in ["", "layout"]:
            return False
        
        # todo: we should be at least a bit more precise
        # (implement XSD based TypeDetector?)
        
        try:
            root = ElementTree.fromstring(data.encode("utf-8"))
            if root.tag != "GUILayout":
                return False
            
            # Layout 2 has no version indication :-(
            # However if there is a version attribute, we can be sure it's not Layout2
            if root.get("version") is not None:
                return False
            
            return True
        
        except:
            return False

class Layout3TypeDetector(compatibility.TypeDetector):
    def getType(self):
        return CEGUILayout3
    
    def getPossibleExtensions(self):
        return set(["layout"])
    
    def matches(self, data, extension):
        if extension not in ["", "layout"]:
            return False
        
        # todo: we should be at least a bit more precise
        # (implement XSD based TypeDetector?)
        
        try:
            root = ElementTree.fromstring(data.encode("utf-8"))
            if root.tag != "GUILayout":
                return False
            
            # Layout 3 has no version indication :-(
            # However if there is a version attribute, we can be sure it's not Layout3
            if root.get("version") is not None:
                return False
            
            return True
        
        except:
            return False

class Layout4TypeDetector(compatibility.TypeDetector):
    def getType(self):
        return CEGUILayout4
    
    def getPossibleExtensions(self):
        return set(["layout"])
    
    def matches(self, data, extension):
        if extension not in ["", "layout"]:
            return False
        
        # todo: we should be at least a bit more precise
        # (implement XSD based TypeDetector?)
        
        try:
            root = ElementTree.fromstring(data.encode("utf-8"))
            if root.tag != "GUILayout":
                return False
            
            if root.get("version", "unknown") != "4":
                return False
            
            return True
        
        except:
            return False
        
class Layout3To4Layer(compatibility.Layer):
    def getSourceType(self):
        return CEGUILayout3
    
    def getTargetType(self):
        return CEGUILayout4
    
    def transformAttribute(self, element, attribute):
        sourceAttributeName = attribute[0].upper() + attribute[1:]
        targetAttributeName = sourceAttributeName[0].lower() + sourceAttributeName[1:]
        
        if element.get(sourceAttributeName) is not None:
            element.set(targetAttributeName, element.get(sourceAttributeName))
            del element.attrib[sourceAttributeName]
    
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
    
    @classmethod
    def transformPropertiesOf(cls, element, tag = "Property", nameAttribute = "Name", valueAttribute = "Value", windowType = None):
        if windowType is None:
            windowType = element.get("Type")
            if windowType is None:
                windowType = ""
                #raise RuntimeError("Can't figure out windowType when transforming properties, tried attribute 'Type'")

        # convert the properties that had 'Unified' prefix
        for property in element.findall(tag):
            name = property.get(nameAttribute, "")
            
            if name == "ZOrderChangeEnabled":
                name = "ZOrderingEnabled"
                
            elif name == "MouseButtonDownAutoRepeat":
                name = "MouseAutoRepeatEnabled"
            
            elif name == "CustomTooltipType":
                name = "TooltipType"
            elif name == "Tooltip":
                name = "TooltipText"
                
            elif name == "RiseOnClick":
                name = "RiseOnClickEnabled"
            
            elif name == "UnifiedAreaRect":
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
                property.set(nameAttribute, name)
        
            def convertImagePropertyToName(property):
                value = property.get(valueAttribute)
                if value is None:
                    value = property.text
                
                split = value.split("image:", 1)
                if len(split) != 2:
                    raise RuntimeError("Failed parsing value '%s' as 0.7 image reference" % (value))
                
                split[0] = split[0][4:] # get rid of "set:"
                
                # strip both of whitespaces left and right
                split[0] = split[0].strip()
                split[1] = split[1].strip()
                
                property.set(valueAttribute, "%s/%s" % (split[0], split[1]))
            
            if windowType.endswith("StaticImage"):
                if name == "Image":
                    convertImagePropertyToName(property)
                    
            elif windowType.endswith("ImageButton"):
                if name in ["NormalImage", "HoverImage", "PushedImage"]:
                    convertImagePropertyToName(property)
                    
            elif windowType.endswith("FrameWindow"):
                if name.endswith("SizingCursorImage"):
                    convertImagePropertyToName(property)
                    
            elif windowType.endswith("ListHeaderSegment"):
                if name in ["MovingCursorImage", "SizingCursorImage"]:
                    convertImagePropertyToName(property)
                    
            else:
                # we have done all explicit migrations, at this point the best we can do is guess
                # if a property name ends with Image, it is most likely an image
                if name.endswith("Image"):
                    try:
                        convertImagePropertyToName(property)
                        
                    except:
                        # best effort only, we don't have enough info
                        pass
    
    def applyChangesRecursively(self, window):
        ret = ""
        
        for layoutImport in window.findall("LayoutImport"):
            self.transformAttribute(layoutImport, "filename")
            self.transformAttribute(layoutImport, "resourceGroup")
            if layoutImport.get("Prefix") is not None:
                # no such thing is available in layout version 4
                del layoutImport.attrib["Prefix"]

        Layout3To4Layer.transformPropertiesOf(window)
        for property in window.findall("Property"):
            property.set("name", property.get("Name"))
            del property.attrib["Name"]
            
            if property.get("Value") is not None:
                property.set("value", property.get("Value"))
                del property.attrib["Value"]
        
        for event in window.findall("Event"):
            self.transformAttribute(event, "name")
            self.transformAttribute(event, "function")
        
        for childWindow in window.findall("Window"):
            self.applyChangesRecursively(childWindow)
        
        for autoWindow in window.findall("AutoWindow"):
            self.convertAutoWindowSuffix(autoWindow)
            self.applyChangesRecursively(childWindow)
        
        if window.get("Name") is not None:
            window.set("name", window.get("Name"))
            del window.attrib["Name"]
        window.set("type", window.get("Type"))
        del window.attrib["Type"]

        return ret
    
    def transform(self, data):
        log = ""
        
        root = ElementTree.fromstring(data.encode("utf-8"))
        
        # version 4 has a version attribute
        root.set("version", "4")
        
        # no parent attribute in layout version 4 (CEGUI 1.0+)
        if root.get("Parent") is not None:
            del root.attrib["Parent"]
        
        for window in root.findall("Window"):
            # should be only one window
            
            # first make the names relative to parent
            log += self.convertToRelativeNames(window)
            
            # apply other changes
            log += self.applyChangesRecursively(window)
            
        return unicode(ElementTree.tostring(root, "utf-8"), encoding = "utf-8")

class Layout4To3Layer(compatibility.Layer):
    def getSourceType(self):
        return CEGUILayout4
    
    def getTargetType(self):
        return CEGUILayout3
    
    def transformAttribute(self, element, attribute):
        targetAttributeName = attribute[0].upper() + attribute[1:]
        sourceAttributeName = targetAttributeName[0].lower() + targetAttributeName[1:]
        
        if element.get(sourceAttributeName) is not None:
            element.set(targetAttributeName, element.get(sourceAttributeName))
            del element.attrib[sourceAttributeName]
    
    def convertToAbsoluteNames(self, window, leadingName = ""):
        ret = ""
        
        name = window.get("name", "")
        if leadingName != "":
            name = leadingName + "/" + name
        
        for childWindow in window.findall("Window"):
            ret += self.convertToAbsoluteNames(childWindow, name)
    
        window.set("name", name)
        
        return ret
    
    def convertAutoWindowSuffix(self, autoWindow):
        autoWindow.set("NameSuffix", autoWindow.get("NamePath"))
        del autoWindow.attrib["NamePath"]
    
        for childAutoWindow in autoWindow.findall("AutoWindow"):
            self.convertAutoWindowSuffix(childAutoWindow)
    
    @classmethod
    def transformPropertiesOf(cls, element, tag = "Property", nameAttribute = "name", valueAttribute = "value", windowType = None):
        if windowType is None:
            windowType = element.get("type")
            if windowType is None:
                windowType = ""
                #raise RuntimeError("Can't figure out windowType when transforming properties, tried attribute 'Type'")
        
        # convert the properties that had 'Unified' prefix in 0.7
        for property in element.findall(tag):
            name = property.get(nameAttribute, "")
            
            if name == "ZOrderingEnabled":
                name = "ZOrderChangeEnabled"
                
            elif name == "MouseAutoRepeatEnabled":
                name = "MouseButtonDownAutoRepeat"
            
            elif name == "TooltipType":
                name = "CustomTooltipType"
            elif name == "TooltipText":
                name = "Tooltip"
                
            elif name == "RiseOnClickEnabled":
                name = "RiseOnClick"

            elif name == "Area":
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
                property.set(nameAttribute, name)
                
            def convertImagePropertyToImagesetImage(property):
                value = property.get(valueAttribute)
                if value is None:
                    value = property.text
                
                split = value.split("/", 1)
                if len(split) != 2:
                    raise RuntimeError("Failed parsing value '%s' as 1.0 image reference" % (value))
                property.set(valueAttribute, "set:%s image:%s" % (split[0], split[1]))
        
            if windowType.endswith("StaticImage"):
                if name == "Image":
                    convertImagePropertyToImagesetImage(property)
                    
            elif windowType.endswith("ImageButton"):
                if name in ["NormalImage", "HoverImage", "PushedImage"]:
                    convertImagePropertyToImagesetImage(property)
                    return
    
            elif windowType.endswith("FrameWindow"):
                if name.endswith("SizingCursorImage"):
                    convertImagePropertyToImagesetImage(property)
                    
            elif windowType.endswith("ListHeaderSegment"):
                if name in ["MovingCursorImage", "SizingCursorImage"]:
                    convertImagePropertyToImagesetImage(property)
                    
            else:
                # we have done all explicit migrations, at this point the best we can do is guess
                # if a property name ends with Image, it is most likely an image
                if name.endswith("Image"):
                    try:
                        convertImagePropertyToImagesetImage(property)
                        
                    except:
                        # best effort only, we don't have enough info
                        pass

    def applyChangesRecursively(self, window):
        ret = ""

        for layoutImport in window.findall("LayoutImport"):
            self.transformAttribute(layoutImport, "filename")
            self.transformAttribute(layoutImport, "resourceGroup")

        Layout4To3Layer.transformPropertiesOf(window)
        for property in window.findall("Property"):
            property.set("Name", property.get("name"))
            del property.attrib["name"]
            
            if property.get("value") is not None:
                property.set("Value", property.get("value"))
                del property.attrib["value"]
        
        for event in window.findall("Event"):
            self.transformAttribute(event, "name")
            self.transformAttribute(event, "function")
        
        for childWindow in window.findall("Window"):
            self.applyChangesRecursively(childWindow)
            
        for autoWindow in window.findall("AutoWindow"):
            self.convertAutoWindowSuffix(autoWindow)
            self.applyChangesRecursively(childWindow)
            
        for userString in window.findall("UserString"):
            raise NotImplementedError("Can't migrate, UserString element is not supported in layout version 3 (up to CEGUI 0.7)")
        
        if window.get("name") is not None:
            window.set("Name", window.get("name"))
            del window.attrib["name"]
        window.set("Type", window.get("type"))
        del window.attrib["type"]

        return ret
    
    def transform(self, data):
        log = ""
        
        root = ElementTree.fromstring(data.encode("utf-8"))
        
        # version 3 must not have a version attribute
        del root.attrib["version"]
        
        for window in root.findall("Window"):
            # should be only one window
            
            # first make the names relative to parent
            log += self.convertToAbsoluteNames(window)
            
            # apply other changes
            log += self.applyChangesRecursively(window)
            
        return unicode(ElementTree.tostring(root, "utf-8"), encoding = "utf-8")
