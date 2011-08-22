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

from PySide import QtCore
from PySide.QtGui import QDockWidget, QLabel, QPushButton, QListView, QFileSystemModel

import ui.filesystembrowser

import os

class FileSystemBrowser(QDockWidget):
    """This class represents the file system browser dock widget, usually located right bottom
    in the main window. It can browse your entire filesystem and if you double click a file
    it will open an editor tab for it.
    """

    fileOpenRequested = QtCore.Signal(str)

    def __init__(self):
        super(FileSystemBrowser, self).__init__()

        self.ui = ui.filesystembrowser.Ui_FileSystemBrowser()
        self.ui.setupUi(self)

        self.view = self.findChild(QListView, "view")
        self.model = QFileSystemModel()
        # causes way too many problems
        #self.model.setReadOnly(False)
        self.view.setModel(self.model)

        self.view.doubleClicked.connect(self.slot_itemDoubleClicked)

        self.parentDirectoryButton = self.findChild(QPushButton, "parentDirectoryButton")
        self.parentDirectoryButton.pressed.connect(self.slot_parentDirectoryButton)
        self.pathDisplay = self.findChild(QLabel, "pathDisplay")

        self.setDirectory(os.curdir)


    def setDirectory(self, directory):
        """Sets the browser to view given directory"""

        directory = os.path.abspath(directory)
        assert(os.path.isdir(directory))

        self.model.setRootPath(directory)
        self.view.setRootIndex(self.model.index(directory));

        self.directory = directory
        self.pathDisplay.setText(self.directory)

    def slot_itemDoubleClicked(self, modelIndex):
        """Slot that gets triggered whenever user double clicks anything
        in the filesystem view
        """

        childPath = modelIndex.data()
        absolutePath = os.path.normpath(os.path.join(self.directory, childPath))

        if (os.path.isdir(absolutePath)):
            self.setDirectory(absolutePath)
        else:
            self.fileOpenRequested.emit(absolutePath)

    def slot_parentDirectoryButton(self):
        """Slot that gets triggered whenever the "Parent Directory" button gets pressed"""
        self.setDirectory(os.path.dirname(self.directory))
