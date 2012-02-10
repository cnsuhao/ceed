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

from PySide import QtGui
from ceed import editors

# TODO: This could get replaced by QScintilla once PySide guys get it to work.
#       Scintilla would probably be overkill though, I can't imagine anyone
#       doing any serious text editing in this application

class TextTabbedEditor(editors.TabbedEditor):
    """Multi purpose text editor
    """
    
    def __init__(self, filePath):
        
        super(TextTabbedEditor, self).__init__(None, filePath)
        
        self.tabWidget = QtGui.QTextEdit()
    
    def initialise(self, mainWindow):
        super(TextTabbedEditor, self).initialise(mainWindow)
            
        file_ = open(self.filePath, "r")
        self.textDocument = QtGui.QTextDocument()
        self.textDocument.setPlainText(file_.read())
        file_.close()
        
        self.tabWidget.setDocument(self.textDocument)
        self.textDocument.setModified(False)

        self.textDocument.setUndoRedoEnabled(True)
        self.textDocument.undoAvailable.connect(self.slot_undoAvailable)
        self.textDocument.redoAvailable.connect(self.slot_redoAvailable)
    
    def finalise(self):
        super(TextTabbedEditor, self).finalise()
        
        self.textDocument = None
        
    def hasChanges(self):
        return self.textDocument.isModified()
    
    def undo(self):
        # TODO: For some weird reason this doesn't do anything, could be a PySide bug
        self.textDocument.undo()
        
    def redo(self):
        # TODO: For some weird reason this doesn't do anything, could be a PySide bug
        self.textDocument.redo()
        
    def slot_undoAvailable(self, available):
        self.mainWindow.undoAction.setEnabled(available)
        
    def slot_redoAvailable(self, available):
        self.mainWindow.redoAction.setEnabled(available)

class TextTabbedEditorFactory(editors.TabbedEditorFactory):
    def getFileExtensions(self):
        extensions = {"py", "lua", "txt", "xml"}
        # this is just temporary, will go away when scheme, looknfeel and font editors are in place
        temporaryExtensions = {"scheme", "looknfeel", "font"}
        extensions.update(temporaryExtensions)
        return extensions

    def canEditFile(self, filePath):
        extensions = self.getFileExtensions()
        
        for extension in extensions:
            if filePath.endswith("." + extension):
                return True
            
        return False

    def create(self, filePath):
        return TextTabbedEditor(filePath)
