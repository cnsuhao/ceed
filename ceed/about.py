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

from PySide import QtGui

import ceed.ui.licensedialog
import ceed.ui.aboutdialog

import version

class LicenseDialog(QtGui.QDialog):
    def __init__(self):
        super(LicenseDialog, self).__init__()

        self.ui = ceed.ui.licensedialog.Ui_LicenseDialog()
        self.ui.setupUi(self)

class AboutDialog(QtGui.QDialog):
    def __init__(self):
        super(AboutDialog, self).__init__()

        self.ui = ceed.ui.aboutdialog.Ui_AboutDialog()
        self.ui.setupUi(self)

        # background
        self.ui.aboutImage.setPixmap(QtGui.QPixmap("images/splashscreen.png"))

        # XXX: In the future, this may not be here.
        CEEDDescription = "- Rejoice in the splendor -"

        self.findChild(QtGui.QLabel, "CEEDDescription").setText("{0}".format(CEEDDescription))
        self.findChild(QtGui.QLabel, "CEEDVersion").setText("CEED: {0}".format(version.CEED))
        self.findChild(QtGui.QLabel, "PySideVersion").setText("PySide: {0}".format(version.PySide))
        self.findChild(QtGui.QLabel, "QtVersion").setText("Qt: {0}".format(version.Qt))
        self.findChild(QtGui.QLabel, "PyCEGUIVersion").setText("PyCEGUI: {0}".format(version.PyCEGUI))
