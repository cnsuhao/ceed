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

import ceed.compatibility.lnf as lnf_compatibility

from ceed.editors.lnf import visual
from ceed.editors.lnf import code
from ceed.editors.lnf import preview

import PyCEGUI

class lnfTabbedEditor(editors.multi.MultiModeTabbedEditor):
    """Binds all lnf editing functionality together
    """

    def __init__(self, filePath):
        super(lnfTabbedEditor, self).__init__(lnf_compatibility.manager, filePath)

        self.requiresProject = True

        self.visual = visual.VisualEditing(self)
        self.addTab(self.visual, "Visual")

        self.code = code.CodeEditing(self)
        self.addTab(self.code, "Code")

        # lnf Previewer is not actually an edit mode, you can't edit the lnf from it,
        # however for everything to work smoothly we do push edit mode changes to it to the
        # undo stack.
        #
        # TODO: This could be improved at least a little bit if 2 consecutive edit mode changes
        #       looked like this: A->Preview, Preview->C.  We could simply turn this into A->C,
        #       and if A = C it would eat the undo command entirely.
        self.previewer = preview.lnfPreviewer(self)
        self.addTab(self.previewer, "Live Preview")

        self.tabWidget = self

        # set the toolbar icon size according to the setting and subscribe to it
        self.tbIconSizeEntry = settings.getEntry("global/ui/toolbar_icon_size")
        self.updateToolbarSize(self.tbIconSizeEntry.value)
        self.tbIconSizeCallback = lambda value: self.updateToolbarSize(value)
        self.tbIconSizeEntry.subscribe(self.tbIconSizeCallback)

    def initialise(self, mainWindow):
        super(lnfTabbedEditor, self).initialise(mainWindow)

        # we have to make the context the current context to ensure textures are fine
        self.mainWindow.ceguiContainerWidget.makeGLContextCurrent()

        root = None
        if self.nativeData != "":
            root = PyCEGUI.WindowManager.getSingleton().loadlnfFromString(self.nativeData)

        self.visual.initialise(root)

    def finalise(self):
        super(lnfTabbedEditor, self).finalise()

    def destroy(self):
        # unsubscribe from the toolbar icon size setting
        self.tbIconSizeEntry.unsubscribe(self.tbIconSizeCallback)

        super(lnfTabbedEditor, self).destroy()

    def rebuildEditorMenu(self, editorMenu):
        editorMenu.setTitle("&lnf")
        self.visual.rebuildEditorMenu(editorMenu)

        return True, self.currentWidget() == self.visual

    def activate(self):
        super(lnfTabbedEditor, self).activate()

        self.mainWindow.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.visual.hierarchyDockWidget)
        self.visual.hierarchyDockWidget.setVisible(True)
        self.mainWindow.addDockWidget(QtCore.Qt.RightDockWidgetArea, self.visual.propertiesDockWidget)
        self.visual.propertiesDockWidget.setVisible(True)
        self.mainWindow.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.visual.createWidgetDockWidget)
        self.visual.createWidgetDockWidget.setVisible(True)
        self.mainWindow.addToolBar(QtCore.Qt.ToolBarArea.TopToolBarArea, self.visual.toolBar)
        self.visual.toolBar.show()

    def updateToolbarSize(self, size):
        if size < 16:
            size = 16
        self.visual.toolBar.setIconSize(QtCore.QSize(size, size))

    def deactivate(self):
        self.mainWindow.removeDockWidget(self.visual.hierarchyDockWidget)
        self.mainWindow.removeDockWidget(self.visual.propertiesDockWidget)
        self.mainWindow.removeDockWidget(self.visual.createWidgetDockWidget)
        self.mainWindow.removeToolBar(self.visual.toolBar)

        super(lnfTabbedEditor, self).deactivate()

    def saveAs(self, targetPath, updateCurrentPath = True):
        codeMode = self.currentWidget() is self.code

        # if user saved in code mode, we process the code by propagating it to visual
        # (allowing the change propagation to do the code validating and other work for us)

        if codeMode:
            self.code.propagateToVisual()

        currentRootWidget = self.visual.getCurrentRootWidget()

        if currentRootWidget is None:
            QtGui.QMessageBox.warning(self.mainWindow, "No root widget in the Look n' Feel!", "I am refusing to save your Look n' Feel, CEGUI Look n' Feel are invalid unless they have a root widget!\n\nPlease create a root widget before saving.")
            return False

        self.nativeData = PyCEGUI.WindowManager.getSingleton().getlnfAsString(currentRootWidget)
        return super(lnfTabbedEditor, self).saveAs(targetPath, updateCurrentPath)

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

class lnfTabbedEditorFactory(editors.TabbedEditorFactory):
    def getFileExtensions(self):
        extensions = lnf_compatibility.manager.getAllPossibleExtensions()
        return extensions

    def canEditFile(self, filePath):
        extensions = self.getFileExtensions()

        for extension in extensions:
            if filePath.endswith("." + extension):
                return True

        return False

    def create(self, filePath):
        return lnfTabbedEditor(filePath)
