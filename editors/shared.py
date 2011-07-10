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

##
# This module contains interfaces that allow editors (of the same type) to share
# toolbars, dockwidgets and possibly more in the future
# 
# Why is this necessary:
# **********************
# To avoid bloating the memory, to allow user to move things around (customize
# the interface) and have that persist when switching to another editor of the
# same type or even when shutting CEED down and starting it up again

# NOTE: This is just experimental code that is not used anywhere (it is used in layout
#       editing but doesn't actually do anything)

class SharedRegistryEntry(object):
    def __init__(self):
        self.currentlyActiveFor = None
    
    def activateFor(self, editor):
        self.impl_activateFor(editor)
        self.currentlyActiveFor = editor
    
    def deactivateFor(self, editor):
        if self.currentlyActiveFor is editor:
            self.impl_deactivateFor(editor)
            self.currentlyActiveFor = None
    
    def impl_activateFor(self, editor):
        raise NotImplementedError("You must implement RegistryEntry.impl_activateFor in the subclasses")
            
    def impl_deactivateFor(self, editor):
        raise NotImplementedError("You must implement RegistryEntry.impl_deactivateFor in the subclasses")

class SharingMixin(object):
    registry = {}
    
    def __init__(self):
        ourType = type(self)
        
        if not SharingMixin.registry.has_key(ourType):
            entry = self.createSharedRegistryEntry()
            SharingMixin.registry[ourType] = entry
        
        self.sharedRegistry = SharingMixin.registry[ourType]
        
    def createSharedRegistryEntry(self):
        raise NotImplementedError("You must implement SharingMixin.createRegistryEntry in the subclasses!")
    
    def activateSharedRegistryEntry(self):
        self.sharedRegistry.activateFor(self)
        
    def deactivateSharedRegistryEntry(self):
        self.sharedRegistry.deactivateFor(self)
        