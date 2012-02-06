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

from ceed import commands

idbase = 1300

class ChangeCurrentAnimationDefinition(commands.UndoCommand):
    """Changes currently edited animation definition.
    
    We have to make this an undo command to be sure that the context for other
    undo commands is always right.
    """
    
    def __init__(self, visual, newName, oldName):
        super(ChangeCurrentAnimationDefinition, self).__init__()
        
        self.visual = visual
        
        self.newName = newName
        self.oldName = oldName
        
        self.refreshText()
    
    def refreshText(self):            
        self.setText("Now editing '%s'" % (self.newName))
                
    def id(self):
        return idbase + 1
        
    def mergeWith(self, cmd):
        self.newName = cmd.newName
        
        return True
    
    def undo(self):
        super(ChangeCurrentAnimationDefinition, self).undo()
        
        if self.oldName is None:
            self.visual.setCurrentAnimation(None)
        else:
            self.visual.setCurrentAnimationWrapper(self.visual.getAnimationWrapper(self.oldName))
            
    def redo(self):
        if self.newName is None:
            self.visual.setCurrentAnimation(None)
        else:
            self.visual.setCurrentAnimationWrapper(self.visual.getAnimationWrapper(self.newName))
            
        super(ChangeCurrentAnimationDefinition, self).redo()
