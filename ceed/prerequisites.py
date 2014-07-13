##############################################################################
#   CEED - Unified CEGUI asset editor
#
#   Copyright (C) 2011-2012   Martin Preisler <martin@preisler.me>
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

"""This module is used to check dependencies of CEED, check their versions
and provide helpful info when something goes wrong.
"""

def check(supressMessagesIfNotFatal = True):
    """Checks all hard dependencies of CEED and reports accordingly
    """

    # We use __import__ in this function merely to stop pyflakes and pylint
    # from reporting unused imports

    def messageBox(message):
        print message

    ret = True
    messages = []

    # PySide
    try:
        __import__("PySide")

    except ImportError as e:
        messages.append("PySide package is missing! PySide provides Python bindings for Qt4, see pyside.org. (exception: %s)" % (e))
        ret = False

    # PyOpenGL
    try:
        __import__("OpenGL.GL")
        __import__("OpenGL.GLU")

    except ImportError as e:
        messages.append("PyOpenGL package is missing! PyOpenGL provides Python bindings for OpenGL, they can be found in the pypi repository. (exception: %s)" % (e))
        ret = False

    # PyCEGUI
    def canImportPyCEGUI():
        try:
            __import__("PyCEGUI")
            __import__("PyCEGUIOpenGLRenderer")

        except ImportError:
            return False

        return True

    # at first we assume the user has PyCEGUI in path and everything is setup
    if not canImportPyCEGUI():
        try:
            # however if that's not the case, we add cegui-0.8 site-packages subdir
            from distutils.sysconfig import get_python_lib
            from os.path import join as path_join
            from sys import path as sys_path
            from sys import platform as sys_platform
            from ceed import compatibility

            # example of the final path: /usr/lib64/python2.7/site-packages/cegui-0.8
            site_packages_path = path_join(get_python_lib(True), "cegui-%s" % (compatibility.EditorEmbeddedCEGUIVersion))
            sys_path.append(site_packages_path)

            if not canImportPyCEGUI() and sys_platform != "win32":
                # maybe CEGUI and PyCEGUI were installed in /usr/local instead of /usr
                site_packages_path = path_join(get_python_lib(True, False, "/usr/local"), "cegui-%s" % (compatibility.EditorEmbeddedCEGUIVersion))
                sys_path.append(site_packages_path)

        except ImportError:
            pass

    try:
        __import__("PyCEGUI")
        try:
            __import__("PyCEGUIOpenGLRenderer")

        except ImportError as e:
            messages.append("PyCEGUI was found but PyCEGUIOpenGLRenderer is missing! CEED can't render embedded CEGUI without it. (exception: %s)" % (e))
            ret = False

    except ImportError as e:
        messages.append("PyCEGUI package is missing! PyCEGUI provides Python bindings for CEGUI, the library this editor edits assets for, see cegui.org.uk. (exception: %s)" % (e))
        ret = False

    # Version module
    from ceed import version

    # Version checking
    if version.PYTHON_TUPLE < (2, 6):
        messages.append("Python is version '%s', at least 2.6 required" % (version.PYTHON))
        ret = False
    if version.PYSIDE_TUPLE < (1, 0, 3):
        messages.append("PySide package is not the required version (found version: '%s')! At least version 1.0.3 is required!" % (version.PYSIDE))
        ret = False
    if version.QT_TUPLE < (4, 7, 0):
        messages.append("Qt is not the required version (found version: '%s')! At least version 4.7 is required!" % (version.QT))
        ret = False

    # Finished
    if (not ret) or (not supressMessagesIfNotFatal and len(messages) > 0):
        messageBox("Following problems found: \n" + unicode("\n").join(messages))

    return ret
