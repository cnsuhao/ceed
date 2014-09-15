##############################################################################
#   CEED - Unified CEGUI asset editor
#
#   Copyright (C) 2011-2014   Martin Preisler <martin@preisler.me>
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

"""Provides messages that users can dismiss (choose to never show again)
"""

from PySide import QtGui

import hashlib

def warning(app, parentWidget, title, message, token = None):
    """Pops up a modal warning dialog, blocks until user dismisses

    app - ceed.Application, we get QSettings from there
    parentWidget - parent Qt widget of the spawned dialog
    title - window title of the spawned dialog
    message - message text, plain text
    token - this is used to remember whether user dismissed to never show again

    token is generated automatically from title and message if None is passed.
    For messages containing diagnostic info this may not be appropriate. The
    info inside will change, thus changing the token and user will see the
    same warning again. Passing a proper descriptive token is advised.
    """

    if app is None:
        app = QtGui.QApplication.instance()

    if token is None:
        token = hashlib.sha1(title + message).hexdigest()

    qsettingsKey = "messages/never_show_warning_%s" % (token)

    if app.qsettings.value(qsettingsKey, False):
        # user chose to never show this type of dialog again
        return

    dialog = QtGui.QMessageBox(parentWidget)

    dialog.setIcon(QtGui.QMessageBox.Icon.Warning)
    dialog.setWindowTitle(title)
    dialog.setText(message)

    dialog.addButton("Ok", QtGui.QMessageBox.ButtonRole.AcceptRole)
    dialog.addButton("Never show again", QtGui.QMessageBox.ButtonRole.RejectRole)

    response = dialog.exec_()

    if response == QtGui.QMessageBox.ButtonRole.RejectRole:
        app.qsettings.setValue(qsettingsKey, True)
