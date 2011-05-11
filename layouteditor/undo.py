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

import commands
import copy

import cegui

idbase = 1200

class MoveCommand(commands.UndoCommand):
    """This command simply moves given widgets from old positions to new
    """
    
    def __init__(self, visual, widgetPaths, oldPositions, newPositions):
        super(MoveCommand, self).__init__()
        
        self.visual = visual
        
        self.widgetPaths = widgetPaths
        self.oldPositions = oldPositions
        self.newPositions = newPositions
    
        self.refreshText()
    
    def refreshText(self):            
        if len(self.widgetPaths) == 1:
            self.setText("Move '%s'" % (self.widgetPaths[0]))
        else:
            self.setText("Move %i widgets" % (len(self.widgetPaths)))
                
    def id(self):
        return idbase + 1
        
    def mergeWith(self, cmd):
        if self.widgetPaths == cmd.widgetPaths:
            # TODO
        
            pass
        
        return False
        
    def undo(self):
        super(MoveCommand, self).undo()
        
        for widgetPath in self.widgetPaths:
            widgetManipulator = self.visual.scene.getWidgetManipulatorByPath(widgetPath)
            widgetManipulator.widget.setPosition(self.oldPositions[widgetPath])
            widgetManipulator.updateFromWidget()
            
    def redo(self):
        for widgetPath in self.widgetPaths:
            widgetManipulator = self.visual.scene.getWidgetManipulatorByPath(widgetPath)
            widgetManipulator.widget.setPosition(self.newPositions[widgetPath])
            widgetManipulator.updateFromWidget()
            
        super(MoveCommand, self).redo()

class ResizeCommand(commands.UndoCommand):
    """This command resizes given widgets from old positions and old sizes to new
    """
    
    def __init__(self, visual, widgetPaths, oldPositions, oldSizes, newPositions, newSizes):
        super(ResizeCommand, self).__init__()
        
        self.visual = visual
        
        self.widgetPaths = widgetPaths
        self.oldPositions = oldPositions
        self.oldSizes = oldSizes
        self.newPositions = newPositions
        self.newSizes = newSizes
    
        self.refreshText()
    
    def refreshText(self):            
        if len(self.widgetPaths) == 1:
            self.setText("Resize '%s'" % (self.widgetPaths[0]))
        else:
            self.setText("Resize %i widgets" % (len(self.widgetPaths)))
                
    def id(self):
        return idbase + 2
        
    def mergeWith(self, cmd):
        if self.widgetPaths == cmd.widgetPaths:
            # TODO
        
            pass
        
        return False
        
    def undo(self):
        super(ResizeCommand, self).undo()
        
        for widgetPath in self.widgetPaths:
            widgetManipulator = self.visual.scene.getWidgetManipulatorByPath(widgetPath)
            widgetManipulator.widget.setPosition(self.oldPositions[widgetPath])
            widgetManipulator.widget.setSize(self.oldSizes[widgetPath])
            widgetManipulator.updateFromWidget()
            
    def redo(self):
        for widgetPath in self.widgetPaths:
            widgetManipulator = self.visual.scene.getWidgetManipulatorByPath(widgetPath)
            widgetManipulator.widget.setPosition(self.newPositions[widgetPath])
            widgetManipulator.widget.setSize(self.newSizes[widgetPath])
            widgetManipulator.updateFromWidget()
            
        super(ResizeCommand, self).redo()

class DeleteCommand(commands.UndoCommand):
    """This command deletes given widgets"""
    
    def __init__(self, visual, widgetPaths):
        super(DeleteCommand, self).__init__()
        
        self.visual = visual
        
        self.widgetPaths = widgetPaths
        self.widgetData = {}
        
        # we have to add all the child widgets of all widgets we are deleting
        for widgetPath in self.widgetPaths:
            manipulator = self.visual.scene.getWidgetManipulatorByPath(widgetPath)
            dependencies = manipulator.getAllDescendantManipulators()
            
            for dependency in dependencies:
                depencencyNamePath = dependency.widget.getNamePath()
                if depencencyNamePath not in self.widgetPaths:
                    self.widgetPaths.append(depencencyNamePath)
        
        # now we have to sort them in a way that ensures the most depending widgets come first
        # (the most deeply nested widgets get deleted first before their ancestors get deleted)
        class ManipulatorDependencyKey(object):
            def __init__(self, visual, path):
                self.visual = visual
                
                self.path = path
                self.manipulator = self.visual.scene.getWidgetManipulatorByPath(path)
                
            def __lt__(self, otherKey):
                # if this is the ancestor of other manipulator, it comes after it
                if self.manipulator.widget.isAncestor(otherKey.manipulator.widget):
                    return True
                # vice versa
                if otherKey.manipulator.widget.isAncestor(self.manipulator.widget):
                    return False
                
                # otherwise, we don't care but lets define a precise order
                return self.path < otherKey.path
        
        self.widgetPaths = sorted(self.widgetPaths, key = lambda path: ManipulatorDependencyKey(self.visual, path))
        
        # we have to store everything about these widgets before we destroy them,
        # we want to be able to restore if user decides to undo
        for widgetPath in self.widgetPaths:
            # serialiseChildren is False because we have already included all the children and they are handled separately
            self.widgetData[widgetPath] = cegui.widget.SerialisationData(self.visual.scene.getWidgetManipulatorByPath(widgetPath).widget,
                                                                         serialiseChildren = False)
        
        self.refreshText()
    
    def refreshText(self):            
        if len(self.widgetPaths) == 1:
            self.setText("Delete '%s'" % (self.widgetPaths[0]))
        else:
            self.setText("Delete %i widgets" % (len(self.widgetPaths)))
        
    def id(self):
        return idbase + 3
        
    def mergeWith(self, cmd):
        # we never merge deletes
        return False
        
    def undo(self):
        super(DeleteCommand, self).undo()
        
        # we have to undo in reverse to ensure widgets have their (potential) dependencies in place when they
        # are constructed
        for widgetPath in reversed(self.widgetPaths):
            data = self.widgetData[widgetPath]
            result = data.reconstruct(self.visual.scene.rootManipulator)
            
            if self.visual.scene.rootManipulator is None:
                # the first that is undone is definitely the root if root is amongst the deleted widgets
                #assert(data.parentPath == "")
                self.visual.scene.rootManipulator = result
                
        self.visual.hierarchyDockWidget.setRootWidgetManipulator(self.visual.scene.rootManipulator)
            
    def redo(self):
        for widgetPath in self.widgetPaths:
            manipulator = self.visual.scene.getWidgetManipulatorByPath(widgetPath)
            manipulator.detach(destroyWidget = True)
            
            if manipulator is self.visual.scene.rootManipulator:
                self.visual.scene.rootManipulator = None
        
        self.visual.hierarchyDockWidget.setRootWidgetManipulator(self.visual.scene.rootManipulator)
        
        super(DeleteCommand, self).redo()

class PropertyEditCommand(commands.UndoCommand):
    """This command resizes given widgets from old positions and old sizes to new
    """
    
    def __init__(self, visual, propertyName, widgetPaths, oldValues, newValue):
        super(PropertyEditCommand, self).__init__()
        
        self.visual = visual
        
        self.propertyName = propertyName
        self.widgetPaths = widgetPaths
        self.oldValues = oldValues
        self.newValue = newValue
        
        self.refreshText()
    
    def refreshText(self):            
        if len(self.widgetPaths) == 1:
            self.setText("Change '%s' in '%s'" % (self.propertyName, self.widgetPaths[0]))
        else:
            self.setText("Change '%s' in %i widgets" % (self.propertyName, len(self.widgetPaths)))
        
    def id(self):
        return idbase + 4
        
    def mergeWith(self, cmd):
        if self.widgetPaths == cmd.widgetPaths:
            # TODO
        
            pass
        
        return False
        
    def undo(self):
        super(PropertyEditCommand, self).undo()
        
        for widgetPath in self.widgetPaths:
            widgetManipulator = self.visual.scene.getWidgetManipulatorByPath(widgetPath)
            widgetManipulator.widget.setProperty(self.propertyName, self.oldValues[widgetPath])
            widgetManipulator.updateFromWidget()
            
    def redo(self):
        for widgetPath in self.widgetPaths:
            widgetManipulator = self.visual.scene.getWidgetManipulatorByPath(widgetPath)
            widgetManipulator.widget.setProperty(self.propertyName, self.newValue)
            widgetManipulator.updateFromWidget()
            
        super(PropertyEditCommand, self).redo()

class XMLEditingCommand(commands.UndoCommand):
    """Extremely memory hungry implementation for now, I have to figure out how to use my own
    QUndoStack with QTextDocument in the future to fix this.
    """
    def __init__(self, xmlediting, oldText, oldCursor, newText, newCursor, totalChange):
        super(XMLEditingCommand, self).__init__()
        
        self.xmlediting = xmlediting
        self.oldText = oldText
        self.oldCursor = copy.copy(oldCursor)
        self.newText = newText
        self.newCursor = copy.copy(newCursor)
        
        self.totalChange = totalChange
        
        self.dryRun = True
        
        self.refreshText()
        
    def refreshText(self):
        if self.totalChange == 1:
            self.setText("XML edit, changed 1 character")
        else:
            self.setText("XML edit, changed %i characters" % (self.totalChange))
        
    def id(self):
        return idbase + 5
        
    def mergeWith(self, cmd):
        assert(self.xmlediting == cmd.xmlediting)
        
        # TODO: 10 chars for now for testing
        if self.totalChange + cmd.totalChange < 10:
            self.totalChange += cmd.totalChange
            self.newText = cmd.newText
            self.newCursor = cmd.newCursor
            
            self.refreshText()
            
            return True
        
        return False
        
    def undo(self):
        super(XMLEditingCommand, self).undo()
        
        self.xmlediting.ignoreUndoCommands = True
        self.xmlediting.setPlainText(self.oldText)
        self.xmlediting.ignoreUndoCommands = False
        #self.xmlediting.setTextCursor(self.oldCursor)
        
    def redo(self):
        if not self.dryRun:
            self.xmlediting.ignoreUndoCommands = True
            self.xmlediting.setPlainText(self.newText)
            self.xmlediting.ignoreUndoCommands = False
            #self.xmlediting.setTextCursor(self.newCursor)
            
        self.dryRun = False

        super(XMLEditingCommand, self).redo()
        