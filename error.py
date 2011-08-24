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

import version

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
        self.tracebackStr = ""
        for line in formattedTraceback:
            self.tracebackStr += line + "\n"

        # Convenience
        def _stamp(newLine, arg):
            self.tracebackStr = '\n'.join([self.tracebackStr, newLine.format(arg)])

        # Mercurial information
        # - The mercurial API is still under development, and can change from
        #   release to release; this may or may not work in the future.
        def _mercurialStamp():
            _stamp('Revision: {0}', version.MercurialRevision)

        # - Operating under the principle that the immediately useful details
        #   should come first, we put the Mercurial/versioning information at
        #   the end.
        def _versionStamp():
            # - If the versioning info was stored in an object, not a module,
            #   we could iterate ... hint hint.
            _stamp('Architecture: {0}', version.SystemArch)
            _stamp('Type: {0}', version.SystemType)
            _stamp('Processor: {0}', version.SystemCore)
            _stamp('OS: {0}', version.OSType)
            _stamp('Release: {0}', version.OSRelease)
            _stamp('Version: {0}', version.OSVersion)
            OSType = version.OSType
            if OSType == 'Windows':
                _stamp('Windows: {0}', version.Windows)
            elif OSType == 'Linux':
                _stamp('Linux: {0}', version.Linux)
            elif OSType == 'Java':
                _stamp('Java: {0}', version.Java)
            elif OSType == 'Darwin':
                _stamp('Darwin: {0}', version.Mac)
            _stamp('Python: {0}', version.Python)
            _stamp('PySide: {0}', version.PySide)
            _stamp('Qt: {0}', version.Qt)
            _stamp('OpenGL: {0}', version.OpenGL)
            _stamp('PyCEGUI: {0}', version.PyCEGUI)
            _stamp('CEED: {0}', version.CEED)
        _mercurialStamp()
        _versionStamp()

        self.details.setPlainText("Exception message: %s\n\n"
                                 "Traceback:\n"
                                 "%s"
                                 % (exc_message, self.tracebackStr))

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
                fp.write(dialog.tracebackStr)

            # we also call the original excepthook which will just output things to stderr
            sys.__excepthook__(exc_type, exc_message, exc_traceback)

            # if the dialog was reject, the user chose to quit the whole app immediately (coward...)
            if result == QDialog.Rejected:
                # stop annoying the user
                self.uninstallExceptionHook()
                # and try to quit as soon as possible
                # we don't care about exception safety/cleaning up at this point
                sys.exit(1)
