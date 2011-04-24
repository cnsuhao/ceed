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

from PySide.QtGui import *
from PySide.QtCore import *

from xml.etree import ElementTree

import sys

import mixedtab

import undo
import xmledit

class XMLParseError(Exception):
    """XML parsing failed"""
    
    def __init__(self, exception):
        self.exception = exception

class XMLEditing(xmledit.XMLEditWidget, mixedtab.EditMode):
    def __init__(self, parent):
        super(XMLEditing, self).__init__()
        
        self.parent = parent
        self.ignoreUndoCommands = False
        self.ignoreRefreshFromVisual = False
        self.lastUndoText = None
        self.lastUndoCursor = None
        
        self.document().setUndoRedoEnabled(False)
        self.document().contentsChange.connect(self.slot_contentsChange)
        
    def refreshFromVisual(self):
        if not self.ignoreRefreshFromVisual:
            element = self.parent.visual.imagesetEntry.saveToElement()
            xmledit.indent(element)
            
            self.ignoreUndoCommands = True
            self.setPlainText(ElementTree.tostring(element, "utf-8"))
            self.ignoreUndoCommands = False
        
    def propagateChangesToVisual(self):
        source = self.document().toPlainText()
        
        # for some reason, Qt calls hideEvent even though the tab widget was never shown :-/
        # in this case the source will be empty and parsing it will fail
        if source == "":
            return
        
        element = None
        # TODO: What if this fails to parse? Do we show a message box that it failed and allow falling back
        #       to the previous visual state or do we somehow correct the XML like editors do?
        try:
            element = ElementTree.fromstring(self.document().toPlainText())
        
        except Exception as e:
            raise XMLParseError(e)
        
        else:
            self.parent.visual.loadImagesetEntryFromElement(element)
        
    def activate(self):
        super(XMLEditing, self).activate()
        self.refreshFromVisual()

    def deactivate(self):
        ret = True
      
        try:
            self.propagateChangesToVisual()
            ret = True
        
        except XMLParseError as e:
            # the file contains more than just CR LF
            result = QMessageBox.question(self,
                                 "Parsing the XML changes failed!",
                                 "Parsing of the changes done in XML edit mode failed, the result wasn't a well-formed XML.\n"
                                 "Press Cancel to stay in the XML edit mode to correct the mistake(s) or press Discard to "
                                 "discard the changes and go back to the previous state (before you entered xml edit mode).\n\n"
                                 "Exception details follow: %s" % (e),
                                 QMessageBox.Cancel | QMessageBox.Discard, QMessageBox.Cancel)
            
            if result == QMessageBox.Cancel:
                # return False to indicate we don't want to switch out of this widget
                ret = False
                # TODO: eat the unnecessary undo commands
                
            elif result == QMessageBox.Discard:
                # we return True, the visual element wasn't touched (the error is thrown before that)
                ret = True
                
        return ret and super(XMLEditing, self).deactivate()

    def slot_contentsChange(self, position, charsRemoved, charsAdded):
        if not self.ignoreUndoCommands:
            totalChange = charsRemoved + charsAdded
            
            cmd = undo.XMLEditingCommand(self, self.lastUndoText, self.lastTextCursor,
                                               self.toPlainText(), self.textCursor(),
                                               totalChange)
            self.parent.undoStack.push(cmd)
            
        self.lastUndoText = self.toPlainText()
        self.lastTextCursor = self.textCursor()
        