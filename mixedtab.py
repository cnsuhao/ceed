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
# This module contains interfaces for mixed editing tabbed editors (visual, source, ...)

import tab
import commands

from PySide.QtGui import QTabWidget

class ModeSwitchCommand(commands.UndoCommand):
    """Undo command that is pushed to the undo stack whenever user switches edit modes.
    
    Switching edit mode has to be an undoable command because the other commands might
    or might not make sense if user is not in the right mode.
    
    This has a drawback that switching to Live Preview (layout editing) and back is
    undoable even though you can't affect the document in any way whilst in Live Preview
    mode.
    """
    def __init__(self, tabbedEditor, oldTabIndex, newTabIndex):
        super(ModeSwitchCommand, self).__init__()
        
        self.tabbedEditor = tabbedEditor
        
        self.oldTabIndex = oldTabIndex
        self.newTabIndex = newTabIndex
        
        # we never every merge edit mode changes, no need to define this as refreshText
        self.setText("Change edit mode to '%s'" % self.tabbedEditor.tabText(newTabIndex))
        
    def undo(self):
        super(ModeSwitchCommand, self).undo()
        
        self.tabbedEditor.ignoreCurrentChangedForUndo = True
        self.tabbedEditor.setCurrentIndex(self.oldTabIndex)
        self.tabbedEditor.ignoreCurrentChangedForUndo = False
            
    def redo(self):
        # to avoid multiple event firing
        if self.tabbedEditor.currentIndex() != self.newTabIndex:
            self.tabbedEditor.ignoreCurrentChangedForUndo = True
            self.tabbedEditor.setCurrentIndex(self.newTabIndex)
            self.tabbedEditor.ignoreCurrentChangedForUndo = False
        
        super(ModeSwitchCommand, self).redo()

class EditMode(object):
    """Interface class for the edit mode widgets (more a mixin class)
    This practically just ensures that the inherited classes have activate and deactivate
    methods.
    """
    
    def __init__(self):
        pass
    
    def activate(self):
        """This is called whenever this edit mode is activated (user clicked on the tab button
        representing it). It's not called when user switches from a different file tab whilst
        this tab was already active when user was switching from this file tab to another one!
        
        Activation can't be canceled and must always happen when requested!
        """
        pass
    
    def deactivate(self):
        """This is called whenever this edit mode is deactivated (user clicked on another tab button
        representing another mode). It's not called when user switches to this file tab from another
        file tab and this edit mode was already active before user switched from the file tab to another
        file tab.
        
        if this returns True, all went well
        if this returns False, the action is terminated and the current edit mode stays in place
        """
        
        return True

class MixedTabbedEditor(tab.UndoStackTabbedEditor, QTabWidget):
    """This class represents tabbed editor that has little tabs on the bottom
    allowing you to switch editing "modes" - visual, code, ...
    
    Not all modes have to be able to edit! Switching modes pushes undo actions
    onto the UndoStack to avoid confusion when undoing. These actions never merge
    together.
    
    You yourself are responsible for putting new tabs into this widget!
    You should not add/remove modes after the construction!
    """

    def __init__(self, filePath):
        tab.UndoStackTabbedEditor.__init__(self, filePath)
        QTabWidget.__init__(self)
        
        self.setTabPosition(QTabWidget.South)
        self.setTabShape(QTabWidget.Triangular)
        
        self.currentChanged.connect(self.slot_currentChanged)
        
        # will be -1, that means no tabs are selected
        self.currentTabIndex = self.currentIndex()
        # when canceling tab transfer we have to switch back and avoid unnecessary deactivate/activate cycle
        self.ignoreCurrentChanged = False
        # to avoid unnecessary undo command pushes we ignore currentChanged if we are
        # inside ModeChangeCommand.undo or redo
        self.ignoreCurrentChangedForUndo = False
        
    def initialise(self, mainWindow):
        super(MixedTabbedEditor, self).initialise(mainWindow)
        
        # the emitted signal only contains the new signal, we have to keep track
        # of the current index ourselves so that we know which one is the "old" one
        # for the undo command
        
        # by this time tabs should have been added so this should not be -1
        self.currentTabIndex = self.currentIndex()
        assert(self.currentTabIndex != -1)
        
    def slot_currentChanged(self, newTabIndex):
        if self.ignoreCurrentChanged:
            return
        
        oldTab = self.widget(self.currentTabIndex)
        newTab = self.widget(newTabIndex)

        if oldTab:
            if not oldTab.deactivate():
                self.ignoreCurrentChanged = True
                self.setCurrentWidget(oldTab)
                self.ignoreCurrentChanged = False
                
                return
        
        if newTab:
            newTab.activate()

        if not self.ignoreCurrentChangedForUndo:
            cmd = ModeSwitchCommand(self, self.currentTabIndex, newTabIndex)
            self.undoStack.push(cmd)
        
        self.currentTabIndex = newTabIndex
        