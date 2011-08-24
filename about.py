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

from PySide.QtGui import *
from ui import licensedialog, aboutdialog

import version

class LicenseDialog(QDialog):
    def __init__(self):
        super(LicenseDialog, self).__init__()

        self.ui = licensedialog.Ui_LicenseDialog()
        self.ui.setupUi(self)

class AboutDialog(QDialog):
    def __init__(self):
        super(AboutDialog, self).__init__()

        self.ui = aboutdialog.Ui_AboutDialog()
        self.ui.setupUi(self)

        # background
        self.ui.aboutImage.setPixmap(QPixmap("images/splashscreen.png"))

        # FIXME: In the future, this will probably be a macro/constant/etc.
        CEEDDescription = "The CEGUI Unified Editor\n- Rejoice in the splendor -"

        self.findChild(QLabel, "CEEDDescription").setText("{0}".format(CEEDDescription))
        self.findChild(QLabel, "CEEDVersion").setText("CEED: {0}".format(version.CEED))
        self.findChild(QLabel, "PySideVersion").setText("PySide: {0}".format(version.PySide))
        self.findChild(QLabel, "QtVersion").setText("Qt: {0}".format(version.Qt))
        self.findChild(QLabel, "PyCEGUIVersion").setText("PyCEGUI: {0}".format(version.PyCEGUI))
