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

The 'prerequisites' module imports us the first time, which populates our
attributes. There is an assumption that versions of dependencies will not
change while CEED is running, which should not be that big of a deal.

Beyond version information, we also store a few other details - e.g. system
architecture - which are used in the event of errors/exceptions.
"""

import platform
import sys
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
    WindowsVersion = platform.win32_ver()
    #sys.getwindowsversion()
elif OSType == 'Linux':
    LinuxVersion = platform.linux_distribution()
elif OSType == 'Java': # Jython
    JavaVersion = platform.java_ver()
elif OSType == 'Darwin': # OSX
    MacVersion = platform.mac_ver()

# Python
PythonVersion = sys.version
PythonVersion_Tuple = sys.version_info

# PySide
PySideVersion = _PySideVersion
PySideVersion_Tuple = _PySideVersion_Tuple

# Qt
QtVersion = _QtVersion

# PyCEGUI
PyCEGUIVersion = _PyCEGUIVersion

# CEED
CEEDVersion = 'snapshot4'
