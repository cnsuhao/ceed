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

import declaration

from PySide.QtCore import Qt
from PySide.QtGui import QIcon, QKeySequence

class ConnectionGroup(object):
    """This object allows you to group signal slot connections and
    disconnect them and connect them again en masse.
    
    Very useful when switching editors
    """
    
    class Connection(object):
        """Very lightweight holding object that represents a signal slot connection.
        Receiver is the Python callable (free function, bound method, lambda function, anything really)
        
        Not intended for use outside the ConnectionGroup class, should be considered internal!
        """
        
        def __init__(self, action, receiver, signalName = "triggered", connectionType = Qt.AutoConnection):
            self.action = action
            self.signalName = signalName
            self.receiver = receiver
            self.connectionType = connectionType
            
            self.connected = False
            
            if not hasattr(self.action, self.signalName):
                raise RuntimeError("Given action doesn't have signal called '%s'!" % (self.signalName))
            
        def connect(self):
            if self.connected:
                raise RuntimeError("This Connection was already connected!")
            
            signal = getattr(self.action, self.signalName)
            signal.connect(self.receiver, self.connectionType)
            
            self.connected = True
            
        def disconnect(self):
            if not self.connected:
                raise RuntimeError("Can't disconnect this Connection, it isn't connected at the moment.")
            
            signal = getattr(self.action, self.signalName)
            signal.disconnect(self.receiver)
            
            self.connected = False
    
    def __init__(self, actionManager = None):
        self.actionManager = actionManager
                
        self.connections = []
    
    def add(self, action, **kwargs):
        if isinstance(action, basestring):
            # allow adding actions by their full names/paths for convenience
            if self.actionManager is None:
                raise RuntimeError("Action added by it's string name but action manager wasn't set, can't retrieve the action object!")
            
            action = self.actionManager.getAction(action)
        
        connection = ConnectionGroup.Connection(action, **kwargs)
        self.connections.append(connection)
        
        return connection
    
    def remove(self, connection, ensureDisconnected = True):
        if not connection in self.connections:
            raise RuntimeError("Can't remove given connection, it wasn't added!")
        
        self.connections.remove(connection)
        
        if ensureDisconnected and connection.connected:
            connection.disconnect()
    
    def connectAll(self):
        for connection in self.connections:
            connection.connect()
    
    def disconnectAll(self):
        for connection in self.connections:
            connection.disconnect()
    
class ActionManager(declaration.ActionManager):
    """This is the CEED's action manager, all the "global" actions are declared in it.
    
    Includes general actions (like Quit, Undo & Redo, File Open, etc...) and also editor specific
    actions (layout align left, ...) - you should use ConnectionGroup for these to connect them when
    your editor is activated and disconnect them when it's deactivated.
    
    See ConnectionGroup
    """
    
    def __init__(self, mainWindow, settings):
        super(ActionManager, self).__init__(mainWindow, settings)
        
        general = self.createCategory(name = "general", label = "General")
        general.createAction(name = "application_settings", label = "Application settings",
                             help = "Displays and allows changes of the application settings (persistent settings)",
                             icon = QIcon("icons/actions/application_settings.png"),
                             defaultShortcut = QKeySequence(QKeySequence.Preferences))
        general.createAction(name = "quit", label = "Quit",
                             help = "Exits the entire application safely with confirmation dialogs for all unsaved data.",
                             icon = QIcon("icons/actions/quit.png"),
                             defaultShortcut = QKeySequence(QKeySequence.Quit))

        project_management = self.createCategory(name = "project_management", label = "Project Management")
        project_management.createAction(name = "project_settings", label = "Project settings",
                                        help = "Displays and allows changes of the project settings (of the currently opened project).",
                                        icon = QIcon("icons/actions/project_settings.png"))

        all_editors = self.createCategory(name = "all_editors", label = "All Editors")
        all_editors.createAction(name = "undo", label = "Undo",
                                 help = "Undoes the last operation (in the currently active tabbed editor)",
                                 icon = QIcon("icons/actions/undo.png"),
                                 defaultShortcut = QKeySequence(QKeySequence.Undo))
        all_editors.createAction(name = "redo", label = "Redo",
                                 help = "Redoes the last undone operation (in the currently active tabbed editor)",
                                 icon = QIcon("icons/actions/redo.png"),
                                 defaultShortcut = QKeySequence(QKeySequence.Redo))
        
