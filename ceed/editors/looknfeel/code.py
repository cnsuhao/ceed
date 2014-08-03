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

from ceed.editors import multi

import PyCEGUI

class CodeEditing(multi.CodeEditMode):
    def __init__(self, tabbedEditor):
        """
        :param tabbedEditor: LookNFeelTabbedEditor
        :return:
        """
        super(CodeEditing, self).__init__()

        self.tabbedEditor = tabbedEditor

    def getNativeCode(self):
        # Returns the Look n' Feel XML string based on all WidgetLookFeels that belong to the Look n' Feel file according to the editor

        # We add every WidgetLookFeel name of this Look N' Feel to a StringSet
        nameSet = self.tabbedEditor.getStringSetOfWidgetLookFeelNames()
        # We parse all WidgetLookFeels as XML to a string
        lookAndFeelString = PyCEGUI.WidgetLookManager.getSingleton().getWidgetLookSetAsString(nameSet)

        lookAndFeelString = self.tabbedEditor.unmapWidgetLookReferences(lookAndFeelString)

        return lookAndFeelString

    def propagateNativeCode(self, code):
        # we have to make the context the current context to ensure textures are fine
        mainwindow.MainWindow.instance.ceguiContainerWidget.makeGLContextCurrent()

        self.tabbedEditor.visual.destroyCurrentPreviewWidget()

        loadingSuccessful = True
        try:
            self.tabbedEditor.mapAndLoadLookNFeelFileString(code)
        except:
            self.tabbedEditor.mapAndLoadLookNFeelFileString(self.tabbedEditor.nativeData)
            loadingSuccessful = False

        self.tabbedEditor.visual.updateToNewTargetWidgetLook()

        return loadingSuccessful

# needs to be at the end, imported to get the singleton
from ceed import mainwindow
