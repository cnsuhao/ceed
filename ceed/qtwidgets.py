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

"""Contains reusable widgets that I haven't found in Qt for some reason
"""

from PySide import QtCore
from PySide import QtGui

import ceed.ui.widgets.filelineedit
import ceed.ui.widgets.keysequencebuttondialog

class FileLineEdit(QtGui.QWidget):
    ExistingFileMode = 1
    NewFileMode = 2
    ExistingDirectoryMode = 3
    
    def __init__(self, parent = None):
        super(FileLineEdit, self).__init__(parent)
        
        self.ui = ceed.ui.widgets.filelineedit.Ui_FileLineEdit()
        self.ui.setupUi(self)
        
        self.filter = "Any file (*.*)"
        
        self.lineEdit = self.findChild(QtGui.QLineEdit, "lineEdit")
        self.browseButton = self.findChild(QtGui.QToolButton, "browseButton")
        
        self.browseButton.pressed.connect(self.slot_browse)
        
        self.mode = FileLineEdit.ExistingFileMode
        self.directoryMode = False
        
        self.startDirectory = lambda: ""
    
    def setText(self, text):
        self.lineEdit.setText(text)
        
    def text(self):
        return self.lineEdit.text()
    
    def slot_browse(self):
        path = None
        
        if self.mode == FileLineEdit.ExistingFileMode:
            path, _ = QtGui.QFileDialog.getOpenFileName(self,
                                                        "Choose a path",
                                                        self.startDirectory(),
                                                        self.filter)
            
        elif self.mode == FileLineEdit.NewFileMode:
            path, _ = QtGui.QFileDialog.getSaveFileName(self,
                                                        "Choose a path",
                                                        self.startDirectory(),
                                                        self.filter)
            
        elif self.mode == FileLineEdit.ExistingDirectoryMode:
            path = QtGui.QFileDialog.getExistingDirectory(self,
                                                          "Choose a directory",
                                                          self.startDirectory())
        
        if path != "":    
            self.lineEdit.setText(path)

class ColourButton(QtGui.QPushButton):
    colourChanged = QtCore.Signal(QtGui.QColor)
    
    colour = property(fset = lambda button, colour: button.setColour(colour),
                      fget = lambda button: button._colour)
    
    def __init__(self, parent = None):
        super(ColourButton, self).__init__(parent)
        
        self.setAutoFillBackground(True)
        # seems to look better on most systems
        self.setFlat(True)
        self.colour = QtGui.QColor(255, 255, 255, 255)
        
        self.clicked.connect(self.slot_clicked)
        
    def setColour(self, colour):
        if not hasattr(self, "_colour") or colour != self._colour:
            self._colour = colour
            self.setStyleSheet("background-color: rgba(%i, %i, %i, %i)" % (colour.red(), colour.green(), colour.blue(), colour.alpha()))
            self.setText("R: %03i, G: %03i, B: %03i, A: %03i" % (colour.red(), colour.green(), colour.blue(), colour.alpha()))
            self.colourChanged.emit(colour)
        
    def slot_clicked(self):
        colour = QtGui.QColorDialog.getColor(self.colour, self, "", QtGui.QColorDialog.ColorDialogOption.ShowAlphaChannel)
        
        if colour.isValid():
            self.colour = colour

class PenButton(QtGui.QPushButton):
    # TODO: This is not implemented at all pretty much
    penChanged = QtCore.Signal(QtGui.QPen)
    
    pen = property(fset = lambda button, pen: button.setPen(pen),
                   fget = lambda button: button._pen)
    
    def __init__(self, parent = None):
        super(PenButton, self).__init__(parent)
        
        self.setAutoFillBackground(True)
        # seems to look better on most systems
        self.setFlat(True)
        self.pen = QtGui.QPen()
        
        self.clicked.connect(self.slot_clicked)
        
    def setPen(self, pen):
        if not hasattr(self, "_pen") or pen != self._pen:
            self._pen = pen
            
            lineStyleStr = ""
            if pen.style() == QtCore.Qt.SolidLine:
                lineStyleStr = "solid"
            elif pen.style() == QtCore.Qt.DashLine:
                lineStyleStr = "dash"
            elif pen.style() == QtCore.Qt.DotLine:
                lineStyleStr = "dot"
            elif pen.style() == QtCore.Qt.DashDotLine:
                lineStyleStr = "dash dot"
            elif pen.style() == QtCore.Qt.DashDotDotLine:
                lineStyleStr = "dash dot dot"
            elif pen.style() == QtCore.Qt.CustomDashLine:
                lineStyleStr = "custom dash"
            else:
                raise RuntimeError("Unknown pen line style!")
            
            capStyleStr = ""
            if pen.capStyle() == QtCore.Qt.FlatCap:
                capStyleStr = "flat"
            elif pen.capStyle() == QtCore.Qt.RoundCap:
                capStyleStr = "round"
            elif pen.capStyle() == QtCore.Qt.SquareCap:
                capStyleStr = "square"
            else:
                raise RuntimeError("Unknown pen cap style!")
            
            joinStyleStr = ""
            if pen.joinStyle() == QtCore.Qt.MiterJoin:
                joinStyleStr = "miter"
            elif pen.joinStyle() == QtCore.Qt.BevelJoin:
                joinStyleStr = "bevel"
            elif pen.joinStyle() == QtCore.Qt.RoundJoin:
                joinStyleStr = "round"
            elif pen.joinStyle() == QtCore.Qt.SvgMiterJoin:
                joinStyleStr = "svg miter"
            else:
                raise RuntimeError("Unknown pen join style!")
                
            self.setText("width: %i, line style: %s, cap style: %s, join style: %s" % (pen.width(), lineStyleStr, capStyleStr, joinStyleStr))
            colour = pen.color()
            self.setStyleSheet("background-color: rgba(%i, %i, %i, %i)" % (colour.red(), colour.green(), colour.blue(), colour.alpha()))
            
            self.penChanged.emit(pen)
        
    def slot_clicked(self):
        # TODO
        pass
    
class KeySequenceButton(QtGui.QPushButton):
    class Dialog(QtGui.QDialog):
        def __init__(self, parent = None):
            super(KeySequenceButton.Dialog, self).__init__(parent)
            
            self.setFocusPolicy(QtCore.Qt.StrongFocus)
            
            self.ui = ceed.ui.widgets.keysequencebuttondialog.Ui_KeySequenceButtonDialog()
            self.ui.setupUi(self)
            
            self.keySequence = QtGui.QKeySequence()
            self.keyCombination = self.findChild(QtGui.QLineEdit, "keyCombination")
            
        def setKeySequence(self, keySequence):
            self.keySequence = keySequence
            self.keyCombination.setText(self.keySequence.toString())
            
        def keyPressEvent(self, event):
            self.setKeySequence(QtGui.QKeySequence(event.modifiers() | event.key()))
    
    keySequenceChanged = QtCore.Signal(QtGui.QKeySequence)
    
    keySequence = property(fset = lambda button, keySequence: button.setKeySequence(keySequence),
                           fget = lambda button: button._keySequence)
    
    def __init__(self, parent = None):
        super(KeySequenceButton, self).__init__(parent)
        
        self.setAutoFillBackground(True)
        self.keySequence = QtGui.QKeySequence()
        
        self.clicked.connect(self.slot_clicked)
        
    def setKeySequence(self, keySequence):
        if not hasattr(self, "_keySequence") or keySequence != self._keySequence:
            self._keySequence = keySequence
            self.setText(keySequence.toString())
            self.keySequenceChanged.emit(keySequence)
        
    def slot_clicked(self):
        dialog = KeySequenceButton.Dialog(self)
        dialog.setKeySequence(self.keySequence)
        
        if dialog.exec_() == QtGui.QDialog.Accepted:
            self.keySequence = dialog.keySequence

class LineEditWithClearButton(QtGui.QLineEdit):
    """A QLineEdit with an inline clear button.
    
    Hitting Escape in the line edit clears it.
    
    Based on http://labs.qt.nokia.com/2007/06/06/lineedit-with-a-clear-button/
    """

    def __init__(self, parent=None):
        super(LineEditWithClearButton, self).__init__(parent)

        btn = self.button = QtGui.QToolButton(self)
        icon = QtGui.QPixmap("icons/widgets/edit-clear.png")
        btn.setIcon(icon)
        btn.setIconSize(icon.size())
        btn.setCursor(QtCore.Qt.ArrowCursor)
        btn.setStyleSheet("QToolButton { border: none; padding: 0px; }")
        btn.hide()

        btn.clicked.connect(self.clear)
        self.textChanged.connect(self.updateCloseButton)

        clearAction = QtGui.QAction(self)
        clearAction.setShortcut(QtGui.QKeySequence("Esc"))
        clearAction.setShortcutContext(QtCore.Qt.ShortcutContext.WidgetShortcut)
        clearAction.triggered.connect(self.clear)
        self.addAction(clearAction)

        frameWidth = self.style().pixelMetric(QtGui.QStyle.PM_DefaultFrameWidth)
        self.setStyleSheet("QLineEdit { padding-right: %ipx; }" % (btn.sizeHint().width() + frameWidth + 1))

        minSizeHint = self.minimumSizeHint()
        self.setMinimumSize(max(minSizeHint.width(), btn.sizeHint().width() + frameWidth * 2 + 2),
                            max(minSizeHint.height(), btn.sizeHint().height() + frameWidth * 2 + 2))

    def resizeEvent(self, event):
        sz = self.button.sizeHint()
        frameWidth = self.style().pixelMetric(QtGui.QStyle.PM_DefaultFrameWidth)
        self.button.move(self.rect().right() - frameWidth - sz.width(),
                         (self.rect().bottom() + 1 - sz.height()) / 2)

    def updateCloseButton(self, text):
        self.button.setVisible(not not text)

def getCheckerboardBrush(halfWidth = 5, halfHeight = 5,
                         firstColour = QtGui.QColor(QtCore.Qt.darkGray),
                         secondColour = QtGui.QColor(QtCore.Qt.gray)):
    """Small helper function that generates a brush usually seen in graphics
    editing tools. The checkerboard brush that draws background seen when
    edited images are transparent
    """
    
    ret = QtGui.QBrush()
    texture = QtGui.QPixmap(2 * halfWidth, 2 * halfHeight)
    painter = QtGui.QPainter(texture)
    painter.fillRect(0, 0, halfWidth, halfHeight, firstColour)
    painter.fillRect(halfWidth, halfHeight, halfWidth, halfHeight, firstColour)
    painter.fillRect(halfWidth, 0, halfWidth, halfHeight, secondColour)
    painter.fillRect(0, halfHeight, halfWidth, halfHeight, secondColour)
    painter.end()
    ret.setTexture(texture)
    
    return ret
