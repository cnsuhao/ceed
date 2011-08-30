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
    def __init__(self):
        super(SplashScreen, self).__init__(QPixmap("images/splashscreen.png"))

        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowFlags(Qt.SplashScreen | Qt.WindowStaysOnTopHint)
        self.showMessage("(imageset editing implemented, limited layout editing possible!) | Version: %s" % (version.CEED), Qt.AlignTop | Qt.AlignRight, Qt.GlobalColor.white)

class Application(QApplication):
    """The central application class
    """

    def __init__(self, argv):
        super(Application, self).__init__(argv)

        self.splash = SplashScreen()
        self.splash.show()

        # this ensures that the splash screen is shown on all platforms
        self.processEvents()

        if version.CEED_developerMode:
            # print info about developer's mode to possibly prevent it being
            # forgotten about when releasing
            print("Developer's mode enabled - recompiling all .ui files...")
            
            # in case we are in the developer's mode,
            # lets compile all UI files to ensure they are up to date
            import compileuifiles
    
            compileuifiles.compileUIFiles("./ui")
            compileuifiles.compileUIFiles("./ui/editors")
            compileuifiles.compileUIFiles("./ui/editors/imageset")
            compileuifiles.compileUIFiles("./ui/editors/layout")
            compileuifiles.compileUIFiles("./ui/widgets")

            print("All .ui files recompiled!")

        self.setOrganizationName("CEGUI")
        self.setOrganizationDomain("cegui.org.uk")
        self.setApplicationName("CEED - CEGUI editor")
        self.setApplicationVersion(version.CEED)

        # import mainwindow
        # (we potentially have to compile all UI files first before this is imported,
        # otherwise out of date compiled .py layouts might be used!)
        import mainwindow

        self.mainWindow = mainwindow.MainWindow(self)
        self.mainWindow.showMaximized()
        self.mainWindow.raise_()
        self.splash.finish(self.mainWindow)

        # import error after UI files have been recompiled
        # - Truncate exception log, if it exists.
        import error
        
        # FIXME: Shouldn't this be done somewhere else? in the error module perhaps?
        with open("EXCEPTION.log", mode="w") as fp:
            pass
        
        self.errorHandler = error.ErrorHandler(self.mainWindow)
        self.errorHandler.installExceptionHook()
