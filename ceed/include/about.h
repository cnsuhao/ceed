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

#ifndef CEED_about_
#define CEED_about_

#include "CEEDBase.h"

"""Implements the License and About dialogs
"""

# TODO: What is LicenseDialog doing in this package?

from PySide import QtGui

#include "ui_LicenseDialog.h"
#include "ui_AboutDialog.h"

from ceed import version


/*!
\brief LicenseDialog

Shows GPLv3 and related info in the UI of the application as
    FSF recommends.

    Almost all of it is in the .ui file, editable with QtDesigner

*/
class LicenseDialog : public QDialog


    def __init__(self):
        super(LicenseDialog, self).__init__()

        self.ui = ceed.ui.licensedialog.Ui_LicenseDialog()
        self.ui.setupUi(self)


/*!
\brief AboutDialog

About/Version dialog shown when user selects Help -> About.

    The main goal is to show versions of various things, we can then tell the
    user to just go to this dialog and tell us the versions when something
    goes wrong for them.

*/
class AboutDialog : public QDialog


    def __init__(self):
        super(AboutDialog, self).__init__()

        self.ui = ceed.ui.aboutdialog.Ui_AboutDialog()
        self.ui.setupUi(self)

        # background, see the data/images directory for SVG source
        self.ui.aboutImage.setPixmap(QtGui.QPixmap("images/splashscreen.png"))

        self.findChild(QtGui.QLabel, "CEEDDescription").setText(
            "Please report any issues to help this project."
        )

        self.findChild(QtGui.QLabel, "CEEDVersion").setText("CEED: %s" % (version.CEED))
        self.findChild(QtGui.QLabel, "PySideVersion").setText("PySide: %s" % (version.PYSIDE))
        self.findChild(QtGui.QLabel, "QtVersion").setText("Qt: %s" % (version.QT))
        self.findChild(QtGui.QLabel, "PyCEGUIVersion").setText("PyCEGUI: %s" % (version.PYCEGUI))

#endif
