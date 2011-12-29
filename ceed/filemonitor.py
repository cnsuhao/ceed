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

from PySide import QtGui, QtCore
from PySide.QtGui import QMessageBox

class FileMonitor(object):
    def __init__(self, parent, fileName, reloadFileCallback):
        self.isActiveWindow = False
        self.fileChanged = False
        self.fileName = fileName
        self.reloadFileCallback = reloadFileCallback
        self.displayingAlert = False
        
        self.monitor = QtCore.QFileSystemWatcher(parent)
        self.monitor.fileChanged.connect(self.slot_fileChanged)
        self.monitor.addPath(fileName)
        
    def slot_fileChanged(self):
        self.fileChanged = True
        if self.isActiveWindow:
            self.displayReloadMessage()
            
    def toggle(self, active):
        self.isActiveWindow = active
        if active and self.fileChanged:
            self.displayReloadMessage()
            
    def changeToNewFile(self, newFile):
        self.monitor.removePath(self.fileName)
        self.monitor.addPath(newFile)
        self.fileName = newFile
        
    def displayReloadMessage(self):
        if not self.displayingAlert:
            self.displayingAlert = True
            msgBox = QMessageBox()
            msgBox.setText("File has been modified externally!")
            msgBox.setInformativeText("Should CEED reload the file? If you click Yes and then save, the contents that were externally changed will be overwritten!")
            msgBox.setStandardButtons(QMessageBox.No | QMessageBox.Yes)
            msgBox.setDefaultButton(QMessageBox.Yes)
            ret = msgBox.exec_()
            self.fileChanged = False
            
            if ret == QMessageBox.Yes:
                self.reloadFileCallback()
                
            self.displayingAlert = False
