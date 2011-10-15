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

from ceed import compatibility
from xml.etree import ElementTree

CEGUIScheme1 = "CEGUI Scheme 1"
CEGUIScheme2 = "CEGUI Scheme 2"
CEGUIScheme3 = "CEGUI Scheme 3"
CEGUIScheme4 = "CEGUI Scheme 4"

class Scheme4TypeDetector(compatibility.TypeDetector):
    def getType(self):
        return CEGUIScheme4
    
    def getPossibleExtensions(self):
        return ["scheme"]
    
    def matches(self, data, extension):
        if extension not in ["", "scheme"]:
            return False
        
        # todo: we should be at least a bit more precise
        # (implement XSD based TypeDetector?)
        return True
