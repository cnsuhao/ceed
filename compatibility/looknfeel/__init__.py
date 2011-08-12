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

import cegui

class Manager(compatibility.Manager):
    """Manager of looknfeel compatibility layers"""
    
    instance = None
    
    def __init__(self):
        super(Manager, self).__init__()
        
        assert(Manager.instance is None)
        Manager.instance = self
        
        self.CEGUIVersionTypes = {
            "0.4" : cegui.CEGUILookNFeel1,
            # we only support non-obsolete major versions
            #"0.5" : cegui.CEGUILookNFeel2,
            "0.5" : cegui.CEGUILookNFeel3,
            "0.6" : cegui.CEGUILookNFeel4,
            # we only support non-obsolete major versions
            #"0.7.0" : cegui.CEGUILookNFeel5,
            "0.7" : cegui.CEGUILookNFeel6, # because of animations, since 0.7.2
            "0.8" : cegui.CEGUILookNFeel7
        }

        self.EditorNativeType = cegui.CEGUILookNFeel7
        
        self.detectors.append(cegui.LookNFeel7TypeDetector())

Manager()
