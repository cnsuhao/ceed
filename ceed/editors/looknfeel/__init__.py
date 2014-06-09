##############################################################################
#   CEED - Unified CEGUI asset editor
#
#   Copyright (C) 2011-2012   Martin Preisler <martin@preisler.me>
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

from PySide import QtCore
from PySide import QtGui

from ceed import settings
from ceed import editors

import ceed.compatibility.looknfeel as looknfeel_compatibility

from ceed.editors.looknfeel import visual
from ceed.editors.looknfeel import code
from ceed.editors.looknfeel import preview

import PyCEGUI

import re


class LookNFeelTabbedEditor(editors.multi.MultiModeTabbedEditor):
    """Binds all Look n' Feel editing functionality together
    """

    def __init__(self, filePath):
        super(LookNFeelTabbedEditor, self).__init__(looknfeel_compatibility.manager, filePath)

        self.editorIDString = str(id(self))

        self.requiresProject = True

        self.visual = visual.LookNFeelVisualEditing(self)
        self.addTab(self.visual, "Visual")

        self.code = code.CodeEditing(self)
        self.addTab(self.code, "Code")

        self.widgetLookNameTuples = []

        # Look n' Feel Previewer is not actually an edit mode, you can't edit the Look n' Feel from it,
        # however for everything to work smoothly we do push edit mode changes to it to the
        # undo stack.
        #
        # TODO: This could be improved at least a little bit if 2 consecutive edit mode changes
        #       looked like this: A->Preview, Preview->C.  We could simply turn this into A->C,
        #       and if A = C it would eat the undo command entirely.
        self.previewer = preview.LookNFeelPreviewer(self)
        self.addTab(self.previewer, "Live Preview")

        self.tabWidget = self

        # The name of the widget we are targeting for editing
        self.targetWidgetLook = ""

        # set the toolbar icon size according to the setting and subscribe to it
        self.tbIconSizeEntry = settings.getEntry("global/ui/toolbar_icon_size")
        self.updateToolbarSize(self.tbIconSizeEntry.value)
        self.tbIconSizeCallback = lambda value: self.updateToolbarSize(value)
        self.tbIconSizeEntry.subscribe(self.tbIconSizeCallback)

    def initialise(self, mainWindow):
        super(LookNFeelTabbedEditor, self).initialise(mainWindow)

        # we have to make the context the current context to ensure textures are fine
        self.mainWindow.ceguiContainerWidget.makeGLContextCurrent()

        self.mapAndLoadLookNFeelFileString()

        self.visual.initialise()

    def mapAndLoadLookNFeelFileString(self):
        # When we are loading a Look n' Feel file we want to load it into CEED in a way it doesn't collide with other LNF definitions stored into CEGUI.
        # To prevent name collisions and also to prevent live-editing of WidgetLooks that are used somewhere in a layout editor simultaneously, we will map the
        # names that we load from a Look n' Feel file in a way that they are unique. We achieve this by editing the WidgetLook names inside the string we loaded from
        # the .looknfeel file, so that the LNF Editor instance's python ID will be prepended to the name. ( e.g.: Vanilla/Button will turn into 18273822/Vanilla/Button )
        # Each Editor is associated with only one LNF file so that this will in effect also guarantee that the WidgetLooks inside the CEGUI system will be uniquely named
        # for each file

        # Modifying the string using regex
        regexPattern = "<\s*WidgetLook\sname\s*=\s*\""
        replaceString = "<WidgetLook name=\"" + self.editorIDString + "/"
        modifiedLookNFeelString = re.sub(regexPattern, replaceString, self.nativeData)
        # Parsing the resulting Look n' Feel
        PyCEGUI.WidgetLookManager.getSingleton().parseLookNFeelSpecificationFromString(modifiedLookNFeelString)

        # We retrieve a list of all WidgetLook names (as tuples of original and new name) that we just mapped for this editor
        self.widgetLookNameTuples = self.getWidgetLookNameMappingTuples()

        self.addMappedWidgetLookFalagardMappings()

        self.visual.lookNFeelWidgetLookSelectorWidget.populateWidgetLookComboBox(self.widgetLookNameTuples)

    def eraseMappedWidgetLooks(self):
        for nameTuple in self.widgetLookNameTuples:
            PyCEGUI.WidgetLookManager.getSingleton().eraseWidgetLook(nameTuple[1])

    def getWidgetLookNameMappingTuples(self):
        # Returns an array containing tuples of the original WidgetLook name and the mapped one
        it = PyCEGUI.WidgetLookManager.getSingleton().getWidgetLookIterator()
        widgetLookNameMappingList = []

        while not it.isAtEnd():
            widgetLookEditModeName = it.getCurrentKey()
            splitResult = widgetLookEditModeName.split('/', 1)

            if len(splitResult) != 2:
                continue

            widgetLookEditorID = splitResult[0]
            widgetLookOriginalName = splitResult[1]

            if widgetLookEditorID == self.editorIDString:
                widgetLookNameTuple = (widgetLookOriginalName, widgetLookEditModeName)
                widgetLookNameMappingList.append(widgetLookNameTuple)

            it.next()

        return widgetLookNameMappingList

    def addMappedWidgetLookFalagardMappings(self):
        # We have to "guess" at least one FalagardWindowMapping - we have to keep in mind that there could theoretically be multiple window mappings for one WidgetLook -  ( which
        # contains a targetType and a renderer ) for our WidgetLook so we can display it.
        # If the user has already loaded .scheme files then we can use the WindowFactoryManager for this purpose:
        for nameTuple in self.widgetLookNameTuples:

            falagardMappingIter = PyCEGUI.WindowFactoryManager.getSingleton().getFalagardMappingIterator()
            while not falagardMappingIter.isAtEnd():

                falagardMapping = falagardMappingIter.getCurrentValue()
                if falagardMapping.d_lookName == nameTuple[0]:
                    PyCEGUI.WindowFactoryManager.getSingleton().addFalagardWindowMapping(nameTuple[1], falagardMapping.d_baseType, nameTuple[1],
                                                                                         falagardMapping.d_rendererType)
                falagardMappingIter.next()

    def removeAddedWidgetLookFalagardMappings(self):
        # Removes all FalagardMappings we previously added
        for nameTuple in self.widgetLookNameTuples:
            PyCEGUI.WindowFactoryManager.getSingleton().removeFalagardWindowMapping(nameTuple[1])

    def finalise(self):
        super(LookNFeelTabbedEditor, self).finalise()

    def destroy(self):
        self.visual.destroy()

        # Remove all FalagardMappings we added
        self.removeAddedWidgetLookFalagardMappings()

        # Erase all mapped WidgetLooks we added
        self.eraseMappedWidgetLooks()

        # unsubscribe from the toolbar icon size setting
        self.tbIconSizeEntry.unsubscribe(self.tbIconSizeCallback)

        super(LookNFeelTabbedEditor, self).destroy()

    def rebuildEditorMenu(self, editorMenu):
        editorMenu.setTitle("&Look and Feel")
        self.visual.rebuildEditorMenu(editorMenu)

        return True, self.currentWidget() == self.visual

    def activate(self):
        super(LookNFeelTabbedEditor, self).activate()

        self.mainWindow.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.visual.lookNFeelWidgetLookSelectorWidget)
        self.visual.lookNFeelWidgetLookSelectorWidget.setVisible(True)

        self.mainWindow.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.visual.lookNFeelHierarchyDockWidget)
        self.visual.lookNFeelHierarchyDockWidget.setVisible(True)

        self.mainWindow.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.visual.lookNFeelPropertyEditorDockWidget)
        self.visual.lookNFeelPropertyEditorDockWidget.setVisible(True)

        self.mainWindow.addToolBar(QtCore.Qt.ToolBarArea.TopToolBarArea, self.visual.toolBar)
        self.visual.toolBar.show()

    def updateToolbarSize(self, size):
        if size < 16:
            size = 16
        self.visual.toolBar.setIconSize(QtCore.QSize(size, size))

    def deactivate(self):
        self.mainWindow.removeDockWidget(self.visual.lookNFeelHierarchyDockWidget)
        self.mainWindow.removeDockWidget(self.visual.lookNFeelWidgetLookSelectorWidget)
        self.mainWindow.removeDockWidget(self.visual.lookNFeelPropertyEditorDockWidget)

        self.mainWindow.removeToolBar(self.visual.toolBar)

        super(LookNFeelTabbedEditor, self).deactivate()

    def saveAs(self, targetPath, updateCurrentPath = True):
        codeMode = self.currentWidget() is self.code

        # if user saved in code mode, we process the code by propagating it to visual
        # (allowing the change propagation to do the code validating and other work for us)

        if codeMode:
            self.code.propagateToVisual()

        return super(LookNFeelTabbedEditor, self).saveAs(targetPath, updateCurrentPath)

    def performCut(self):
        if self.currentWidget() is self.visual:
            return self.visual.performCut()

        return False

    def performCopy(self):
        if self.currentWidget() is self.visual:
            return self.visual.performCopy()

        return False

    def performPaste(self):
        if self.currentWidget() is self.visual:
            return self.visual.performPaste()

        return False

    def performDelete(self):
        if self.currentWidget() is self.visual:
            return self.visual.performDelete()

        return False

    def zoomIn(self):
        if self.currentWidget() is self.visual:
            self.visual.scene.views()[0].zoomIn()

    def zoomOut(self):
        if self.currentWidget() is self.visual:
            self.visual.scene.views()[0].zoomOut()

    def zoomReset(self):
        if self.currentWidget() is self.visual:
            self.visual.scene.views()[0].zoomOriginal()


class LookNFeelTabbedEditorFactory(editors.TabbedEditorFactory):
    def getFileExtensions(self):
        extensions = looknfeel_compatibility.manager.getAllPossibleExtensions()
        return extensions

    def canEditFile(self, filePath):
        extensions = self.getFileExtensions()

        for extension in extensions:
            if filePath.endswith("." + extension):
                return True

        return False

    def create(self, filePath):
        return LookNFeelTabbedEditor(filePath)
