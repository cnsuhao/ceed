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

import sys
import os

from PySide.QtCore import Qt, QTimer, QPoint
from PySide.QtGui import QApplication, QSplashScreen, QPixmap

import compileuifiles

def fixCwd():
    """Sets CWD as the applications install directory"""
    
    # this is necessary when starting the app via shortcuts
    
    def getInstallDir():
        import fake
        
        dir = os.path.dirname(os.path.abspath(fake.__file__))

        if dir.endswith("library.zip"):
            # if this is a frozen copy, we have to strip library.zip
            dir = os.path.dirname(dir)
            
        return dir

    os.chdir(getInstallDir())

class SplashScreen(QSplashScreen):
    """A fancy splashscreen that fades out when user moves mouse over it or clicks it.
    """
    
    # TODO: It's modal and when you move the mouse over the application, it doesn't hide
    #       itself/fade out so user always has to me the mouse over the splashscreen
    
    def __init__(self):
        super(SplashScreen, self).__init__(QPixmap("images/splashscreen.png"))
        
        self.lastMousePosition = None
        
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.setWindowModality(Qt.ApplicationModal)
        self.setMouseTracking(True)
        
        self.fadeTimer = QTimer(self)
        self.fadeTimer.timeout.connect(self.fadeTicker)

        self.showMessage("(Only imageset editing implemented!) | Version: pre-release", Qt.AlignTop | Qt.AlignRight, Qt.GlobalColor.white)
        
    def mouseMoveEvent(self, event):
        if not self.lastMousePosition:
            self.lastMousePosition = event.pos()
            
        delta = event.pos() - self.lastMousePosition

        if delta.manhattanLength() > 10:
            self.fadeOut()
        
    def mousePressEvent(self, event):
        self.fadeOut()

    def fadeOut(self):
        # 10 msec interval = 50 fps
        self.fadeTimer.start(20)

    def fadeTicker(self):
        newOpacity = self.windowOpacity() - 0.003 * self.fadeTimer.interval()
        if newOpacity < 0:
            self.fadeTimer.stop()
            self.close()
            return
        
        self.setWindowOpacity(newOpacity)
        self.move(self.pos() + QPoint(0, 1))
        self.update()

class Application(QApplication):
    """The central application class
    """
    
    def __init__(self, argv):
        super(Application, self).__init__(argv)
        
        # first recompile all UI files to ensure they are up to date
        compileuifiles.compileUIFiles("./ui")
        compileuifiles.compileUIFiles("./ui/editors")
        compileuifiles.compileUIFiles("./ui/editors/imageset")
        compileuifiles.compileUIFiles("./ui/editors/layout")
        compileuifiles.compileUIFiles("./ui/widgets")

        self.setOrganizationName("CEGUI")
        self.setOrganizationDomain("cegui.org.uk")
        self.setApplicationName("CEED - CEGUI editor")
        self.setApplicationVersion("0.1 - WIP")
        
        self.splash = SplashScreen()
        self.splash.show()
        
        # import mainwindow after UI files have been recompiled
        import mainwindow
        
        self.mainWindow = mainwindow.MainWindow(self)
        self.mainWindow.showMaximized()
        
        # import error after UI files have been recompiled
        import error
        self.errorHandler = error.ErrorHandler(self.mainWindow)
        self.errorHandler.installExceptionHook()

def main():
    fixCwd()
    
    app = Application(sys.argv)
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
