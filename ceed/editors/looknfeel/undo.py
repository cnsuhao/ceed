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

from ceed import commands

from ceed.editors.looknfeel import widgethelpers
import PyCEGUI

idbase = 1200


class TargetWidgetChangeCommand(commands.UndoCommand):
    """This command changes the Look n' Feel widget targeted for editing to another one
    """

    def __init__(self, visual, tabbedEditor, newTargetWidgetLook):
        """
        :param visual: LookNFeelVisualEditing
        :param tabbedEditor: LookNFeelTabbedEditor
        :param newTargetWidgetLook: string
        :return:
        """
        super(TargetWidgetChangeCommand, self).__init__()

        self.visual = visual

        self.tabbedEditor = tabbedEditor
        self.oldTargetWidgetLook = tabbedEditor.targetWidgetLook
        self.newTargetWidgetLook = newTargetWidgetLook

        self.refreshText()

    def refreshText(self):
        self.setText("Change the target of Look n' Feel editing from widget \"" + self.oldTargetWidgetLook + "\" to \"" + self.newTargetWidgetLook + "\"")

    def id(self):
        return idbase + 15

    def mergeWith(self, cmd):
        return False

    def undo(self):
        super(TargetWidgetChangeCommand, self).undo()

        self.tabbedEditor.targetWidgetLook = self.oldTargetWidgetLook
        self.tabbedEditor.visual.displayNewTargetWidgetLook()

        if self.tabbedEditor.targetWidgetLook == "":
            self.tabbedEditor.visual.lookNFeelPropertyEditorDockWidget.inspector.setSource(None)
        else:
            widgetLookObject = PyCEGUI.WidgetLookManager.getSingleton().getWidgetLook(self.tabbedEditor.targetWidgetLook)
            self.tabbedEditor.visual.lookNFeelPropertyEditorDockWidget.inspector.setSource(widgetLookObject)

        self.tabbedEditor.visual.lookNFeelHierarchyDockWidget.updateWidgetLookFeelHierarchy()

    def redo(self):
        self.tabbedEditor.targetWidgetLook = self.newTargetWidgetLook
        self.tabbedEditor.visual.displayNewTargetWidgetLook()

        if self.tabbedEditor.targetWidgetLook == "":
            self.tabbedEditor.visual.lookNFeelPropertyEditorDockWidget.inspector.setSource(None)
        else:
            widgetLookObject = PyCEGUI.WidgetLookManager.getSingleton().getWidgetLook(self.tabbedEditor.targetWidgetLook)
            self.tabbedEditor.visual.lookNFeelPropertyEditorDockWidget.inspector.setSource(widgetLookObject)

        self.tabbedEditor.visual.lookNFeelHierarchyDockWidget.updateWidgetLookFeelHierarchy()

        super(TargetWidgetChangeCommand, self).redo()