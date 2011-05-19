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

Project1 = "CEED Project 1"

class Project1TypeDetector(compatibility.TypeDetector):
    def getType(self):
        return Project1
    
    def matches(self, data, extension):
        if extension not in ["", "project"]:
            return False
        
        # should work as a pretty rigorous test for now, tests the root tag name and version
        try:
            root = ElementTree.fromstring(data)
            
            if root.tag != "Project":
                return False
            
            if root.get("version", "") != Manager.instance.EditorNativeType:
                return False
        
            return True

        except:
            return False

class Manager(compatibility.Manager):
    """Manager of CEED project compatibility layers"""
    
    instance = None
    
    def __init__(self):
        super(Manager, self).__init__()
        
        assert(Manager.instance is None)
        Manager.instance = self
        
            
        self.EditorNativeType = Project1
        # doesn't make much sense
        self.CEGUIVersionType = {
            "0.6" : Project1,
            "0.7" : Project1,
            "0.8" : Project1
        }
        
        self.detectors.append(Project1TypeDetector())

Manager()
