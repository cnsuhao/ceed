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

from PySide.QtCore import Qt
from PySide.QtGui import QApplication, QSplashScreen, QPixmap

import version

class SplashScreen(QSplashScreen):
    """A fancy splashscreen that fades out when user moves mouse over it or clicks it.
    """
    
    # TODO: It's modal and when you move the mouse over the application, it doesn't hide
    #       itself/fade out so user always has to me the mouse over the splashscreen
    
    def __init__(self):
        super(SplashScreen, self).__init__(QPixmap("images/splashscreen.png"))

        self.showMessage("(imageset editing implemented, limited layout editing possible!) | Version: %s" % (version.getAsString()), Qt.AlignTop | Qt.AlignRight, Qt.GlobalColor.white)

class Application(QApplication):
    """The central application class
    """
    
    def __init__(self, argv):
        super(Application, self).__init__(argv)

        self.splash = SplashScreen()
        self.splash.show()
        
        self.processEvents()
        
        # first recompile all UI files to ensure they are up to date
        import compileuifiles
        
        compileuifiles.compileUIFiles("./ui")
        compileuifiles.compileUIFiles("./ui/editors")
        compileuifiles.compileUIFiles("./ui/editors/imageset")
        compileuifiles.compileUIFiles("./ui/editors/layout")
        compileuifiles.compileUIFiles("./ui/widgets")

        self.setOrganizationName("CEGUI")
        self.setOrganizationDomain("cegui.org.uk")
        self.setApplicationName("CEED - CEGUI editor")
        self.setApplicationVersion(version.getAsString())
        
        # import mainwindow after UI files have been recompiled
        import mainwindow
        
        self.mainWindow = mainwindow.MainWindow(self)
        self.mainWindow.showMaximized()
        self.splash.finish(self.mainWindow)
        
        # import error after UI files have been recompiled
        import error
        self.errorHandler = error.ErrorHandler(self.mainWindow)
        self.errorHandler.installExceptionHook()
