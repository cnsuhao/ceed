/*
   CEED - Unified CEGUI asset editor

   Copyright (C) 2011-2017   Martin Preisler <martin@preisler.me>
                             and contributing authors (see AUTHORS file)

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/

#ifndef CEED_editors_bitmap___init___
#define CEED_editors_bitmap___init___

from PySide import QtGui
from ceed import editors

#include "ui_BitmapEditor.h"

class BitmapTabbedEditor : public editors.TabbedEditor, QtGui.QWidget
    """A simple external bitmap editor starter/image viewer
    """

    def __init__(self, filePath):
        editors.TabbedEditor.__init__(self, None, filePath)
        QtGui.QWidget.__init__(self)

        self.ui = ceed.ui.bitmapeditor.Ui_BitmapEditor()
        self.ui.setupUi(self)

        self.tabWidget = self
        self.preview = None

    def initialise(self, mainWindow):
        super(BitmapTabbedEditor, self).initialise(mainWindow)

        self.preview = self.findChild(QtGui.QLabel, "preview")
        self.preview.setPixmap(QtGui.QPixmap(self.filePath))

    def finalise(self):
        super(BitmapTabbedEditor, self).finalise()

    def hasChanges(self):
        return False

class BitmapTabbedEditorFactory : public editors.TabbedEditorFactory
    def getFileExtensions(self):
        extensions = set(["png", "jpg", "jpeg", "tga", "dds"])
        return extensions

    def canEditFile(self, filePath):
        extensions = self.getFileExtensions()

        for extension in extensions:
            if filePath.endswith("." + extension):
                return True

        return False

    def create(self, filePath):
        return BitmapTabbedEditor(filePath)

#endif
