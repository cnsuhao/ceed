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
        # we return either the current WidgetLook's XML code as string or nothing, if no WidgetLook is selected
        currentWidgetLook = self.tabbedEditor.targetWidgetLook

        if currentWidgetLook is None:
            return ""
        else:
            widgetLookString = PyCEGUI.WidgetLookManager.getSingleton().getWidgetLookAsString(currentWidgetLook)
            return widgetLookString

    def propagateNativeCode(self, code):
        # we have to make the context the current context to ensure textures are fine
        mainwindow.MainWindow.instance.ceguiContainerWidget.makeGLContextCurrent()

        currentWidgetLook = self.tabbedEditor.targetWidgetLook
        codeAccepted = True

        if (code == "") | (currentWidgetLook == ""):
            self.tabbedEditor.tryUpdateWidgetLookFromString("", "")

        else:
            try:
                self.tabbedEditor.tryUpdateWidgetLookFromString(currentWidgetLook, code)
            except:
                codeAccepted = False

            self.tabbedEditor.visual.displayNewTargetWidgetLook()

        return codeAccepted

# needs to be at the end, imported to get the singleton
from ceed import mainwindow
