from PySide import QtGui, QtCore
from PySide.QtGui import QMessageBox

class filemonitor():
    def __init__(self, parent, fileName, method):
        self.isActiveWindow = False
        self.fileChanged = False
        self.fileName = fileName
        self.methodOnYes = method
        self.displayingAlert = False
        self.monitor = QtCore.QFileSystemWatcher(parent)
        QtCore.QObject.connect(self.monitor,QtCore.SIGNAL("fileChanged(const QString&)"), self.__activate__)
        self.monitor.addPath(fileName)
    def __activate__(self):
        self.fileChanged = True
        if self.isActiveWindow:
            self.displayReloadMessage()
    def toggle(self, switch):
        self.isActiveWindow = switch
        if switch and self.fileChanged:
            self.displayReloadMessage()
    def changeToNewFile(self, newFile):
        self.monitor.removePath(self.fileName)
        self.monitor.addPath(newFile)
        self.fileName = newFile
    def displayReloadMessage(self):
        if not self.displayingAlert:
            self.displayingAlert = True
            msgBox = QMessageBox()
            msgBox.setText("An outside program modified the file.")
            msgBox.setInformativeText("Reload the file?")
            msgBox.setStandardButtons(QMessageBox.No | QMessageBox.Yes)
            msgBox.setDefaultButton(QMessageBox.Yes)
            ret = msgBox.exec_()
            self.fileChanged = False
            if ret == QMessageBox.Yes:
                self.methodOnYes()
            self.displayingAlert = False

