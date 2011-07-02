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

from PySide.QtCore import *
from PySide.QtGui import *
import ui.widgets.filelineedit

# Contains reusable widgets that I haven't found in Qt for some reason

# TODO: ColourButton

class FileLineEdit(QWidget):
    ExistingFileMode = 1
    NewFileMode = 2
    ExistingDirectoryMode = 3
    
    def __init__(self, parent = None):
        super(FileLineEdit, self).__init__(parent)
        
        self.ui = ui.widgets.filelineedit.Ui_FileLineEdit()
        self.ui.setupUi(self)
        
        self.filter = "Any file (*.*)"
        
        self.lineEdit = self.findChild(QLineEdit, "lineEdit")
        self.browseButton = self.findChild(QPushButton, "browseButton")
        
        self.browseButton.pressed.connect(self.slot_browse)
        
        self.mode = FileLineEdit.ExistingFileMode
        self.directoryMode = False
    
    def setText(self, text):
        self.lineEdit.setText(text)
        
    def text(self):
        return self.lineEdit.text()
    
    def slot_browse(self):
        path = None
        if self.mode == FileLineEdit.ExistingFileMode:
            path, filter = QFileDialog.getOpenFileName(self,
                               "Choose a path",
                               "",
                               self.filter)
            
        elif self.mode == FileLineEdit.NewFileMode:
            path, filter = QFileDialog.getSaveFileName(self,
                               "Choose a path",
                               "",
                               self.filter)
        elif self.mode == FileLineEdit.ExistingDirectoryMode:
            path = QFileDialog.getExistingDirectory(self, "Choose a directory")
        
        if path != "":    
            self.lineEdit.setText(path)

class ColourButton(QPushButton):
    colourChanged = Signal(QColor)
    
    colour = property(fset = lambda button, colour: button.setColour(colour),
                      fget = lambda button: button._colour)
    
    def __init__(self, parent = None):
        super(ColourButton, self).__init__(parent)
        
        self.setAutoFillBackground(True)
        # seems to look better on most systems
        self.setFlat(True)
        self.colour = QColor(255, 255, 255, 255)
        
        self.clicked.connect(self.slot_clicked)
        
    def setColour(self, colour):
        if not hasattr(self, "_colour") or colour != self._colour:
            self._colour = colour
            self.setStyleSheet("background-color: rgb(%i, %i, %i, %i)" % (colour.red(), colour.green(), colour.blue(), colour.alpha()))
            self.setText("R: %03i, G: %03i, B: %03i, A: %03i" % (colour.red(), colour.green(), colour.blue(), colour.alpha()))
            self.colourChanged.emit(colour)
        
    def slot_clicked(self):
        colour = QColorDialog.getColor(self.colour, self, "", QColorDialog.ColorDialogOption.ShowAlphaChannel)
        
        if colour.isValid():
            self.colour = colour
