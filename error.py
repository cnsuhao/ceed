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

from PySide.QtGui import QDialog, QTextBrowser

# FIXME: There is a problem here - it is possible for a user to have retrieved
# a copy of CEED from a place other than Mercurial; in such an event, they may
# not have this module.
from mercurial import hg
from mercurial import ui as mercui

from version import *

import ui.exceptiondialog

class ExceptionDialog(QDialog):
    """This is a dialog that gets shown whenever an exception is thrown and
    isn't caught. This is realised via duck overriding the sys.excepthook.
    """

    # Long term TODO:
    # Add an option to pack all the relevant data and error messages to a zip
    # file for easier to reproduce bug reports.

    def __init__(self, exc_type, exc_message, exc_traceback):
        super(ExceptionDialog, self).__init__()

        self.ui = ui.exceptiondialog.Ui_ExceptionDialog()
        self.ui.setupUi(self)

        self.details = self.findChild(QTextBrowser, "details")

        self.setWindowTitle("Exception %s" % (exc_type))

        import traceback
        formattedTraceback = traceback.format_tb(exc_traceback)
        tracebackStr = ""
        for line in formattedTraceback:
            tracebackStr += line + "\n"

        # Mercurial information
        # - The mercurial API is still under development, and can change from
        #   release to release; this may or may not work in the future.
        def _mercurialStamp():
            ret = ''
            repo = hg.repository(mercui.ui(), '.')
            ret = '\n'.join([ret, 'Repo: {0}'.format(repo.ui.config('paths', 'default'))])
            ret = '\n'.join([ret, 'Branch: {0}'.format(repo[None].branch())])
            return ret
        tracebackStr = ''.join([tracebackStr, _mercurialStamp()])

        # - Operating under the principle that the immediately useful details
        #   should come first, we put the Mercurial/versioning information at
        #   the end.
        def _versionStamp():
            # - If the versioning info was stored in an object, not a module,
            #   we could iterate ... hint hint.
            ret = ''
            ret = '\n'.join([ret, 'Architecture: {0}'.format(SystemArch)])
            ret = '\n'.join([ret, 'Type: {0}'.format(SystemType)])
            ret = '\n'.join([ret, 'Processor: {0}'.format(SystemCore)])
            ret = '\n'.join([ret, 'OS: {0}'.format(OSType)])
            ret = '\n'.join([ret, 'Release: {0}'.format(OSRelease)])
            ret = '\n'.join([ret, 'Version: {0}'.format(OSVersion)])
            if OSType == 'Windows':
                ret = '\n'.join([ret, 'Windows: {0}'.format(WindowsVersion)])
            elif OSType == 'Linux':
                ret = '\n'.join([ret, 'Linux: {0}'.format(LinuxVersion)])
            elif OSType == 'Java':
                ret = '\n'.join([ret, 'Java: {0}'.format(JavaVersion)])
            elif OSType == 'Darwin':
                ret = '\n'.join([ret, 'Darwin: {0}'.format(MacVersion)])
            ret = '\n'.join([ret, 'Python: {0}'.format(PythonVersion)])
            ret = '\n'.join([ret, 'PySide: {0}'.format(PySideVersion)])
            ret = '\n'.join([ret, 'Qt: {0}'.format(QtVersion)])
            ret = '\n'.join([ret, 'PyCEGUI: {0}'.format(PyCEGUIVersion)])
            ret = '\n'.join([ret, 'CEED: {0}'.format(CEEDVersion)])
            return ret
        tracebackStr = '\n'.join([tracebackStr, _versionStamp()])
        self.errorStr = tracebackStr

        self.details.setPlainText("Exception message: %s\n\n"
                                 "Traceback:\n"
                                 "%s"
                                 % (exc_message, tracebackStr))

class ErrorHandler(object):
    """This class is responsible for all error handling. It only handles exceptions for now.
    """

    # TODO: handle stderr messages as soft errors

    def __init__(self, mainWindow):
        self.mainWindow = mainWindow

    def installExceptionHook(self):
        sys.excepthook = self.excepthook

    def uninstallExceptionHook(self):
        sys.excepthook = sys.__excepthook__

    def excepthook(self, exc_type, exc_message, exc_traceback):
        if not self.mainWindow:
            sys.__excepthook__(exc_type, exc_message, exc_traceback)

        else:
            dialog = ExceptionDialog(exc_type, exc_message, exc_traceback)
            result = dialog.exec_()

            # Dump to file, to ease bug reporting (e-mail attachments, etc)
            # - In the future, this could be mailed as a bug report?
            with open('EXCEPTION.log', mode='w') as fp:
                fp.write(dialog.errorStr)

            # we also call the original excepthook which will just output things to stderr
            sys.__excepthook__(exc_type, exc_message, exc_traceback)

            # if the dialog was reject, the user chose to quit the whole app immediately (coward...)
            if result == QDialog.Rejected:
                # stop annoying the user
                self.uninstallExceptionHook()
                # and try to quit as soon as possible
                # we don't care about exception safety/cleaning up at this point
                sys.exit(1)
