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
# This module contains interfaces needed to run editors tabs (multi-file editing)
# Also groups all the editors together to avoid cluttering the root directory

from PySide.QtCore import *
from PySide.QtGui import *

import os.path
from ceed import compatibility

import ceed.ui.editors.notypedetected
import ceed.ui.editors.multipletypesdetected
import ceed.ui.editors.multiplepossiblefactories

class NoTypeDetectedDialog(QDialog):
    def __init__(self, compatibilityManager):
        super(NoTypeDetectedDialog, self).__init__()

        self.ui = ceed.ui.editors.notypedetected.Ui_NoTypeDetectedDialog()
        self.ui.setupUi(self)
        
        self.typeChoice = self.findChild(QListWidget, "typeChoice")
        
        for type in compatibilityManager.getKnownTypes():
            item = QListWidgetItem()
            item.setText(type)
            
            # TODO: We should give a better feedback about what's compatible with what
            item.setToolTip("Compatible with CEGUI: %s" % (", ".join(compatibilityManager.getCEGUIVersionsCompatibleWithType(type))))
            
            self.typeChoice.addItem(item)

class MultipleTypesDetectedDialog(QDialog):
    def __init__(self, compatibilityManager, possibleTypes):
        super(MultipleTypesDetectedDialog, self).__init__()
        
        self.ui = ceed.ui.editors.multipletypesdetected.Ui_MultipleTypesDetectedDialog()
        self.ui.setupUi(self)
        
        self.typeChoice = self.findChild(QListWidget, "typeChoice")
        
        for type in compatibilityManager.getKnownTypes():
            item = QListWidgetItem()
            item.setText(type)
            
            if type in possibleTypes:
                font = QFont()
                font.setBold(True)
                item.setFont(font)
            
            # TODO: We should give a better feedback about what's compatible with what
            item.setToolTip("Compatible with CEGUI: %s" % (", ".join(compatibilityManager.getCEGUIVersionsCompatibleWithType(type))))
            
            self.typeChoice.addItem(item)

class MultiplePossibleFactoriesDialog(QDialog):
    def __init__(self, possibleFactories):
        super(MultiplePossibleFactoriesDialog, self).__init__()
        
        self.ui = ceed.ui.editors.multiplepossiblefactories.Ui_MultiplePossibleFactoriesDialog()
        self.ui.setupUi(self)
        
        self.factoryChoice = self.findChild(QListWidget, "factoryChoice")
        
        for factory in possibleFactories:
            item = QListWidgetItem()
            item.setText(factory.getName())
            item.setData(Qt.UserRole, factory)
            
            self.factoryChoice.addItem(item)

class TabbedEditor(object):
    """This is the base class for a class that takes a file and allows manipulation
    with it. It occupies exactly 1 tab space.
    """
    
    def __init__(self, compatibilityManager, filePath):
        """Constructs the editor.
        
        compatibilityManager - manager that should be used to transform data between
                               various data types using compatibility layers
        filePath - absolute file path of the file that should be opened
        """
        
        self.compatibilityManager = compatibilityManager
        self.desiredSavingDataType = "" if self.compatibilityManager is None else self.compatibilityManager.EditorNativeType
        self.nativeData = None
        
        self.requiresProject = False
        
        self.initialised = False
        self.active = False
        
        self.filePath = os.path.normpath(filePath)
        
        self.tabWidget = None
        self.tabLabel = os.path.basename(self.filePath)
    
    def initialise(self, mainWindow):
        """This method loads everything up so this editor is ready to be switched to"""
        
        assert(not self.initialised)
        assert(self.tabWidget)
        
        self.mainWindow = mainWindow
        self.tabWidget.tabbedEditor = self
        
        self.mainWindow.tabs.addTab(self.tabWidget, self.tabLabel)
        
        if self.compatibilityManager is not None:
            rawData = open(self.filePath, "r").read()
            rawDataType = ""
            
            if rawData == "":
                # it's an empty new file, the derived classes deal with this separately
                self.nativeData = rawData
                
                if mainWindow.project is None:
                    self.desiredSavingDataType = self.compatibilityManager.EditorNativeType
                else:
                    self.desiredSavingDataType = self.compatibilityManager.getSuitableDataTypeForCEGUIVersion(mainWindow.project.CEGUIVersion)
                
            else:
                try:
                    rawDataType = self.compatibilityManager.guessType(rawData, self.filePath)
                    
                except compatibility.NoPossibleTypesError:
                    dialog = NoTypeDetectedDialog(self.compatibilityManager)
                    result = dialog.exec_()
                    
                    rawDataType = self.compatibilityManager.EditorNativeType
                    self.nativeData = ""
                    
                    if result == QDialog.Accepted:
                        selection = dialog.typeChoice.selectedItems()
                        
                        if len(selection) == 1:
                            rawDataType = selection[0].text()
                            self.nativeData = None
                
                except compatibility.MultiplePossibleTypesError as e:
                    # if no project is opened or if the opened file was detected as something not suitable for the target CEGUI version of the project
                    if (mainWindow.project is None) or (self.compatibilityManager.getSuitableDataTypeForCEGUIVersion(mainWindow.project.CEGUIVersion) not in e.possibleTypes):
                        dialog = MultipleTypesDetectedDialog(self.compatibilityManager, e.possibleTypes)
                        result = dialog.exec_()
                        
                        rawDataType = self.compatibilityManager.EditorNativeType
                        self.nativeData = ""
                        
                        if result == QDialog.Accepted:
                            selection = dialog.typeChoice.selectedItems()
                            
                            if len(selection) == 1:
                                rawDataType = selection[0].text()
                                self.nativeData = None
                                
                    else:
                        rawDataType = self.compatibilityManager.getSuitableDataTypeForCEGUIVersion(mainWindow.project.CEGUIVersion)
                        self.nativeData = None
                
                # by default, save in the same format as we opened in
                self.desiredSavingDataType = rawDataType
    
                # if nativeData is "" at this point, data type was not successful and user didn't select
                # any data type as well so we will just use given file as an empty file
                
                if self.nativeData != "":
                    try:
                        self.nativeData = self.compatibilityManager.transform(rawDataType, self.compatibilityManager.EditorNativeType, rawData)
                        
                    except compatibility.LayerNotFoundError:
                        # TODO: Dialog, can't convert
                        self.nativeData = ""
        
        self.initialised = True
    
    def finalise(self):
        """Cleans up after itself and removes itself from the tab list
        this is usually called when you want the tab  closed
        """
        
        assert(self.initialised)
        assert(self.tabWidget)
        
        i = 0
        wdt = self.mainWindow.tabs.widget(i)
        tabRemoved = False
        
        while wdt:
            if wdt == self.tabWidget:
                self.mainWindow.tabs.removeTab(i)
                tabRemoved = True
                break
                        
            i = i + 1
            wdt = self.mainWindow.tabs.widget(i)
        
        assert(tabRemoved)
        
        self.initialised = False
    
    def activate(self):
        """The tab gets "on stage", it's been clicked on and is now the only active
        tab. There can be either 0 tabs active (blank screen) or exactly 1 tab
        active.
        """
        
        currentActive = self.mainWindow.activeEditor
        
        # no need to deactivate and then activate again
        if currentActive == self:
            return
        
        if currentActive is not None:
            currentActive.deactivate()
        
        self.active = True

        self.mainWindow.activeEditor = self
        self.mainWindow.undoViewer.setUndoStack(self.getUndoStack())
        
    def deactivate(self):
        """The tab gets "off stage", user switched to another tab.
        This is also called when user closes the tab (deactivate and then finalise
        is called).
        """
        
        self.active = False
        
        if self.mainWindow.activeEditor == self:
            self.mainWindow.activeEditor = None
    
    def makeCurrent(self):
        """Makes this tab editor current (= the selected tab)"""
        
        # (this should automatically handle the respective deactivate and activate calls)   
        
        self.mainWindow.tabs.setCurrentWidget(self.tabWidget)
 
    def hasChanges(self):
        """Checks whether this TabbedEditor contains changes
        (= it should be saved before closing it)"""
        
        return False

    def markHasChanges(self, hasChanges):
        """Marks that this tabbed editor has changes, in this implementation this means
        that the tab in the tab list gets an icon
        """
        
        if not hasattr(self, "mainWindow"):
            return
        
        if hasChanges:
            self.mainWindow.tabs.setTabIcon(self.mainWindow.tabs.indexOf(self.tabWidget), QIcon("icons/tabs/has_changes.png"))
        else:
            self.mainWindow.tabs.setTabIcon(self.mainWindow.tabs.indexOf(self.tabWidget), QIcon())

    def saveAs(self, targetPath, updateCurrentPath = True):
        """Causes the tabbed editor to save all it's progress to the file.
        targetPath should be absolute file path.
        """
        
        outputData = self.nativeData
        if self.compatibilityManager is not None:
            outputData = self.compatibilityManager.transform(self.compatibilityManager.EditorNativeType, self.desiredSavingDataType, self.nativeData)
        
        f = open(targetPath, "w")
        f.write(outputData)
        f.close()
        
        if updateCurrentPath:
            # changes current path to the path we saved to
            self.filePath = targetPath
            
            # update tab text
            self.tabLabel = os.path.basename(self.filePath)
        
            # hasattr because this might be called even before initialise is called!
            if hasattr(self, "mainWindow"):
                self.mainWindow.tabs.setTabText(self.mainWindow.tabs.indexOf(self.tabWidget), self.tabLabel)

    def save(self):
        """Saves all progress to the same file we have opened at the moment
        """
        
        self.saveAs(self.filePath)

    def discardChanges(self):
        """Causes the tabbed editor to discard all it's progress"""
        
        # early out
        if not self.hasChanges():
            return
        
        # the default but kind of wasteful implementation
        
        # we better store this because it's not specified anywhere that the
        # tabbed editor shouldn't set it to None when finalising, etc...
        mainWindow = self.mainWindow
        
        self.deactivate()
        self.finalise()
        
        self.initialise(mainWindow)
        self.activate()
        
        # the state of the tabbed editor should be valid at this point
        
    def undo(self):
        """Called by the mainwindow whenever undo is requested"""
        pass
        
    def redo(self):
        """Called by the mainwindow whenever redo is requested"""
        pass
    
    def getUndoStack(self):
        """Returns UndoStack or None is the tabbed editor doesn't have undo stacks.
        This is useful for QUndoView
        
        Note: If you use UndoStack in your tabbed editor, inherit from UndoStackTabbedEditor
              below, it will save you a lot of work (synchronising all the actions and their texts, etc..)
        """
        
        return None
    
    def getDesiredSavingDataType(self):
        """Returns current desired saving data type. Data type that will be used when user requests to save this file
        """
        
        return self.desiredSavingDataType if self.compatibilityManager is not None else None

    def performCopy(self):
        """Performs copy of the editor's selection to the clipboard.
        
        Default implementation doesn't do anything.
        
        Returns: True if the operation was successful
        """
        return False
    
    def performCut(self):
        """Performs cut of the editor's selection to the clipboard.
        
        Default implementation doesn't do anything.
        
        Returns: True if the operation was successful
        """
        return False
    
    def performPaste(self):
        """Performs paste from the clipboard to the editor.
        
        Default implementation doesn't do anything
        
        Returns: True if the operation was successful
        """
        return False

    def find(self):
        """Searches for items in the currently active editor.

        Default implementation doesn't do anything

        Returns: True if the operation was successful
        """
        return False

class UndoStackTabbedEditor(TabbedEditor):
    """Used for tabbed editors that have one shared undo stack. This saves a lot
    of boilerplate code for undo/redo action synchronisation and the undo/redo itself
    """
    
    def __init__(self, compatibilityManager, filePath):
        super(UndoStackTabbedEditor, self).__init__(compatibilityManager, filePath)
        
        self.undoStack = QUndoStack()
        
        self.undoStack.setUndoLimit(settings.getEntry("global/undo/limit").value)
        self.undoStack.setClean()
        
        self.undoStack.canUndoChanged.connect(self.slot_undoAvailable)
        self.undoStack.canRedoChanged.connect(self.slot_redoAvailable)
        
        self.undoStack.undoTextChanged.connect(self.slot_undoTextChanged)
        self.undoStack.redoTextChanged.connect(self.slot_redoTextChanged)
        
        self.undoStack.cleanChanged.connect(self.slot_cleanChanged)
        
    def initialise(self, mainWindow):
        super(UndoStackTabbedEditor, self).initialise(mainWindow)
        self.undoStack.clear()
        
    def activate(self):
        super(UndoStackTabbedEditor, self).activate()
        
        self.mainWindow.undoAction.setEnabled(self.undoStack.canUndo())
        self.mainWindow.redoAction.setEnabled(self.undoStack.canRedo())
        
        self.mainWindow.undoAction.setText("Undo %s" % (self.undoStack.undoText()))
        self.mainWindow.redoAction.setText("Redo %s" % (self.undoStack.redoText()))
        
        self.mainWindow.saveAction.setEnabled(not self.undoStack.isClean())
    
    def hasChanges(self):
        return not self.undoStack.isClean()

    def saveAs(self, targetPath, updateCurrentPath = True):
        super(UndoStackTabbedEditor, self).saveAs(targetPath, updateCurrentPath)
        
        self.undoStack.setClean()
        
    def undo(self):
        self.undoStack.undo()
        
    def redo(self):
        self.undoStack.redo()

    def getUndoStack(self):
        return self.undoStack

    def slot_undoAvailable(self, available):
        # hasattr because this might be called even before initialise is called!
        if hasattr(self, "mainWindow"):
            self.mainWindow.undoAction.setEnabled(available)
        
    def slot_redoAvailable(self, available):
        # hasattr because this might be called even before initialise is called!
        if hasattr(self, "mainWindow"):
            self.mainWindow.redoAction.setEnabled(available)
            
    def slot_undoTextChanged(self, text):
        # hasattr because this might be called even before initialise is called!
        if hasattr(self, "mainWindow"):
            self.mainWindow.undoAction.setText("Undo %s" % (text))
            
    def slot_redoTextChanged(self, text):
        # hasattr because this might be called even before initialise is called!
        if hasattr(self, "mainWindow"):
            self.mainWindow.redoAction.setText("Redo %s" % (text))
            
    def slot_cleanChanged(self, clean):
        # clean means that the undo stack is at a state where it's in sync with the underlying file
        # we set the undostack as clean usually when saving the file so we will assume that there
        if hasattr(self, "mainWindow"):
            self.mainWindow.saveAction.setEnabled(not clean)

        self.markHasChanges(not clean)
        
class TabbedEditorFactory(object):
    """Constructs instances of TabbedEditor (multiple instances of one TabbedEditor
    can coexist - user editing 2 layouts for example - with the ability to switch
    from one to another) 
    """
    
    def canEditFile(self, filePath):
        """This checks whether instance created by this factory can edit given file"""
        return False

    def create(self, filePath):
        """Creates the respective TabbedEditor instance
    
        This should only be called with a filePath the factory reported
        as editable by the instances
        """
        
        return None
        
    # note: destroy doesn't really make sense as python is reference counted
    #       and everything is garbage collected

class MessageTabbedEditor(TabbedEditor):
    """This is basically a stub tabbed editor, it simply displays a message
    and doesn't allow any sort of editing at all, all functionality is stubbed

    This is for internal use only so there is no factory for this particular editor
    """
    def __init__(self, filePath, message):
        super(MessageTabbedEditor, self).__init__(None, filePath)
        
        self.message = message
        self.tabWidget = QLabel(self.message)
        self.tabWidget.setWordWrap(True)
        
    def hasChanges(self):
        return False

from ceed import settings
