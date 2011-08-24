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

"""
This module is used as a centrepoint to gather version info

Beyond version information, we also store a few other details - e.g. system
architecture - which are used in the event of errors/exceptions.
"""

import platform
import sys

from OpenGL.version import __version__ as _OpenGLVersion
from PySide import __version__ as _PySideVersion
from PySide import __version_info__ as _PySideVersion_Tuple
from PySide.QtCore import __version__ as _QtVersion
from PyCEGUI import Version__ as _PyCEGUIVersion


# Architecture
SystemArch = platform.architecture()
SystemType = platform.machine()
SystemCore = platform.processor()

# OS agnostic
OSType = platform.system()
OSRelease = platform.release()
OSVersion = platform.version()

# OS specific
if OSType == 'Windows':
    Windows = platform.win32_ver()
    #sys.getwindowsversion()
elif OSType == 'Linux':
    Linux = platform.linux_distribution()
elif OSType == 'Java': # Jython
    Java = platform.java_ver()
elif OSType == 'Darwin': # OSX
    Mac = platform.mac_ver()

# Python
Python = sys.version
Python_Tuple = sys.version_info

# PySide
PySide = _PySideVersion
PySide_Tuple = _PySideVersion_Tuple

# Qt
Qt = _QtVersion

# PyOpenGL
OpenGL = _OpenGLVersion

# PyCEGUI
PyCEGUI = _PyCEGUIVersion

# CEED
CEED = 'snapshot4'

# Mercurial
MercurialRevision = '$MERCURIAL_REVISION$'
