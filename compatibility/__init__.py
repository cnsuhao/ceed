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

class Layer(object):
    """Compatibility layer can transform given code from source type to target type and back"""
    
    def getSourceType(self):
        raise NotImplementedError("Compatibility layers have to override Layer.getSourceType!")
    
    def getTargetType(self):
        raise NotImplementedError("Compatibility layers have to override Layer.getTargetType!")
    
    def transform(self, code):
        """Transforms given code from sourceType (== self.getSourceType())
        to targetType (== self.getTargetType())
        """
        
        raise NotImplementedError("Compatibility layers have to override Layer.transform!")
    
class TypeDetector(object):
    def getType(self):
        """Gets the type this detector detects"""
        
        raise NotImplementedError("Compatibility type detectors have to override TypeDetector.getType!")
    
    def matches(self, code, extension):
        """Checks whether given source code and extension match this detector's type"""
        
        raise NotImplementedError("Compatibility type detectors have to override TypeDetector.getType!")
    
class Manager(object):
    def __init__(self):
        self.detectors = []
        self.layers = []
    
    def transform(self, sourceType, targetType, code):
        """Performs transformation of given source code from sourceType to targetType.
        
        TODO: This method doesn't even bother to try to find the shortest path possible or such,
              I leave this as an exercise for future generations :-D
        """
        
        # special case:
        if sourceType == targetType:
            return code
        
        for layer in self.layers:
            if layer.getSourceType() == sourceType:
                try:
                    return self.transform(layer.getTargetType(), targetType, layer.transform(code))
                
                except RuntimeError as e:
                    # this path doesn't lead anywhere,
                    # lets try to find another one
                    print e
                
        raise RuntimeError("Can't find any compatibility path from sourceType '%s' to targetType '%s'" % (sourceType, targetType))
    
    def guessType(self, code, extension = ""):
        extSplit = extension.rsplit(".", 1)
        extension = ""
        if len(extSplit) > 0:
            extension = extSplit[1] if len(extSplit) == 2 else extSplit[0]
        
        ret = []
        
        print "code: '%s'" % (code)
        print "extension: '%s'" % (extension)
        
        for detector in self.detectors:
            if detector.matches(code, extension):
                ret.append(detector.getType())
                
        if len(ret) > 1:
            raise RuntimeError("Can't decide type of given code and extension, multiple positives turned up!")
        
        if len(ret) == 0:
            raise RuntimeError("Can't decide type of given code and extension, no positives turned up!")
        
        return ret[0]
    
    def transformTo(self, targetType, code, extension):
        """Transforms given code to given target type.
        
        extension is optional and used as a hint for the type guessing, you can pass the full file path,
        extension will be extracted.
        """
            
        sourceType = self.guessType(code, extension)
        return self.transform(sourceType, targetType, code) 
    
import imageset
