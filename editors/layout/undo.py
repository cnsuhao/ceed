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

import widgethelpers
import PyCEGUI

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
            self.widgetData[widgetPath] = widgethelpers.SerialisationData(self.visual, self.visual.scene.getWidgetManipulatorByPath(widgetPath).widget,
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
        
        manipulators = []
        
        # we have to undo in reverse to ensure widgets have their (potential) dependencies in place when they
        # are constructed
        for widgetPath in reversed(self.widgetPaths):
            data = self.widgetData[widgetPath]
            result = data.reconstruct(self.visual.scene.rootManipulator)
            
            if result.widget.getParent() is None:
                # this is a root widget being reconstructed, handle this accordingly
                self.visual.setRootWidgetManipulator(result)
        
            manipulators.append(result)
        
        self.visual.notifyWidgetManipulatorsAdded(manipulators)
        
    def redo(self):
        for widgetPath in self.widgetPaths:
            manipulator = self.visual.scene.getWidgetManipulatorByPath(widgetPath)
            wasRootWidget = manipulator.widget.getParent() is None
                            
            manipulator.detach(destroyWidget = True)
        
            if wasRootWidget:
                # this was a root widget being deleted, handle this accordingly
                self.visual.setRootWidgetManipulator(None)
                
        self.visual.notifyWidgetManipulatorsRemoved(self.widgetPaths)
        
        super(DeleteCommand, self).redo()

class CreateCommand(commands.UndoCommand):
    """This command creates one widget"""
    
    def __init__(self, visual, parentWidgetPath, widgetType, widgetName):
        super(CreateCommand, self).__init__()
        
        self.visual = visual
        
        self.parentWidgetPath = parentWidgetPath
        self.widgetType = widgetType
        self.widgetName = widgetName
        
        self.refreshText()
    
    def refreshText(self):
        self.setText("create '%s' of type '%s'" % (self.widgetName, self.widgetType))
        
    def id(self):
        return idbase + 4
        
    def mergeWith(self, cmd):
        # we never merge deletes
        return False
        
    def undo(self):
        super(CreateCommand, self).undo()
        
        manipulator = self.visual.scene.getWidgetManipulatorByPath(self.parentWidgetPath + "/" + self.widgetName if self.parentWidgetPath != "" else self.widgetName)
        manipulator.detach(destroyWidget = True)
        
        self.visual.hierarchyDockWidget.refresh()
        
    def redo(self):
        data = widgethelpers.SerialisationData(self.visual)

        data.name = self.widgetName
        data.type = self.widgetType
        data.parentPath = self.parentWidgetPath
        
        result = data.reconstruct(self.visual.scene.rootManipulator)
        # if the size is 0x0, the widget will be hard to deal with, lets fix that in that case
        if result.widget.getSize() == PyCEGUI.USize(PyCEGUI.UDim(0, 0), PyCEGUI.UDim(0, 0)):
            result.widget.setSize(PyCEGUI.USize(PyCEGUI.UDim(0, 50), PyCEGUI.UDim(0, 50)))
        
        result.updateFromWidget()
        # ensure this isn't obscured by it's parent
        result.moveToFront()
        
        # the first created widget must be the root (every created widget must have a parent)
        if self.visual.scene.rootManipulator is None:
            self.visual.scene.rootManipulator = result
                
        self.visual.hierarchyDockWidget.setRootWidgetManipulator(self.visual.scene.rootManipulator)
        
        self.visual.hierarchyDockWidget.refresh()
        
        super(CreateCommand, self).redo()

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
        return idbase + 5
        
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

class HorizontalAlignCommand(commands.UndoCommand):
    """This command aligns selected widgets accordingly
    """
    
    def __init__(self, visual, widgetPaths, oldAlignments, newAlignment):
        super(HorizontalAlignCommand, self).__init__()
        
        self.visual = visual
        
        self.widgetPaths = widgetPaths
        self.oldAlignments = oldAlignments
        self.newAlignment = newAlignment
    
        self.refreshText()
    
    def refreshText(self):            
        alignStr = ""
        if self.newAlignment == PyCEGUI.HA_LEFT:
            alignStr = "left"
        elif self.newAlignment == PyCEGUI.HA_CENTRE:
            alignStr = "centre"
        elif self.newAlignment == PyCEGUI.HA_RIGHT:
            alignStr = "right"
        else:
            raise RuntimeError("Unknown horizontal alignment")
        
        if len(self.widgetPaths) == 1:
            self.setText("Horizontal align '%s' %s" % (self.widgetPaths[0], alignStr))
        else:
            self.setText("Horizontal align %i widgets %s" % (len(self.widgetPaths), alignStr))
                
    def id(self):
        return idbase + 6
        
    def mergeWith(self, cmd):
        if self.widgetPaths == cmd.widgetPaths:
            # TODO
        
            pass
        
        return False
        
    def undo(self):
        super(HorizontalAlignCommand, self).undo()
        
        for widgetPath in self.widgetPaths:
            widgetManipulator = self.visual.scene.getWidgetManipulatorByPath(widgetPath)
            widgetManipulator.widget.setHorizontalAlignment(self.oldAlignments[widgetPath])
            widgetManipulator.updateFromWidget()
            
    def redo(self):
        for widgetPath in self.widgetPaths:
            widgetManipulator = self.visual.scene.getWidgetManipulatorByPath(widgetPath)
            widgetManipulator.widget.setHorizontalAlignment(self.newAlignment)
            widgetManipulator.updateFromWidget()
            
        super(HorizontalAlignCommand, self).redo()

class VerticalAlignCommand(commands.UndoCommand):
    """This command aligns selected widgets accordingly
    """
    
    def __init__(self, visual, widgetPaths, oldAlignments, newAlignment):
        super(VerticalAlignCommand, self).__init__()
        
        self.visual = visual
        
        self.widgetPaths = widgetPaths
        self.oldAlignments = oldAlignments
        self.newAlignment = newAlignment
    
        self.refreshText()
    
    def refreshText(self):            
        alignStr = ""
        if self.newAlignment == PyCEGUI.VA_TOP:
            alignStr = "top"
        elif self.newAlignment == PyCEGUI.VA_CENTRE:
            alignStr = "centre"
        elif self.newAlignment == PyCEGUI.VA_BOTTOM:
            alignStr = "bottom"
        else:
            raise RuntimeError("Unknown vertical alignment")
        
        if len(self.widgetPaths) == 1:
            self.setText("Vertical align '%s' %s" % (self.widgetPaths[0], alignStr))
        else:
            self.setText("Vertical align %i widgets %s" % (len(self.widgetPaths), alignStr))
                
    def id(self):
        return idbase + 7
        
    def mergeWith(self, cmd):
        if self.widgetPaths == cmd.widgetPaths:
            # TODO
        
            pass
        
        return False
        
    def undo(self):
        super(VerticalAlignCommand, self).undo()
        
        for widgetPath in self.widgetPaths:
            widgetManipulator = self.visual.scene.getWidgetManipulatorByPath(widgetPath)
            widgetManipulator.widget.setVerticalAlignment(self.oldAlignments[widgetPath])
            widgetManipulator.updateFromWidget()
            
    def redo(self):
        for widgetPath in self.widgetPaths:
            widgetManipulator = self.visual.scene.getWidgetManipulatorByPath(widgetPath)
            widgetManipulator.widget.setVerticalAlignment(self.newAlignment)
            widgetManipulator.updateFromWidget()
            
        super(VerticalAlignCommand, self).redo()
