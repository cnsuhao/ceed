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

# CEED
CEED = "snapshot6"
# if this is True, all .ui files will be recompiled every time CEED.py is run
CEED_developerMode = False

# Mercurial
try:
    import subprocess
        
    MercurialRevision = subprocess.Popen(["hg", "log", "-l", "1", "--template", "Revision:{node|short} ({author})"], stdout = subprocess.PIPE).stdout.read()
    if MercurialRevision.startswith("Revision:"):
        MercurialRevision = MercurialRevision[9:]
    else:
        MercurialRevision = "Unknown"
except:
    MercurialRevision = "Can't execute \"hg\""

import platform
import sys

# Architecture
SystemArch = platform.architecture()
SystemType = platform.machine()
SystemCore = platform.processor()

# OS agnostic
OSType = platform.system()
OSRelease = platform.release()
OSVersion = platform.version()

# OS specific
if OSType == "Windows":
    Windows = platform.win32_ver()
    #sys.getwindowsversion()
elif OSType == "Linux":
    Linux = platform.linux_distribution()
elif OSType == "Java": # Jython
    Java = platform.java_ver()
elif OSType == "Darwin": # OSX
    Mac = platform.mac_ver()

# Python
Python = sys.version
Python_Tuple = sys.version_info

# in case the try block fails, set all the tuples and values to something
PySide = "N/A"
PySide_Tuple = ("N", "/", "A")

Qt = "N/A"
Qt_Tuple = ("N", "/", "A")

OpenGL = "N/A"

PyCEGUI = "N/A"

try:    
    # PySide
    from PySide import __version__ as _PySideVersion
    from PySide import __version_info__ as _PySideVersion_Tuple
    PySide = _PySideVersion
    PySide_Tuple = _PySideVersion_Tuple
    
    # Qt
    from PySide.QtCore import __version__ as _QtVersion
    from PySide.QtCore import __version_info__ as _QtVersion_Tuple
    Qt = _QtVersion
    Qt_Tuple = _QtVersion_Tuple
    
    # PyOpenGL
    from OpenGL.version import __version__ as _OpenGLVersion
    OpenGL = _OpenGLVersion
    
    # PyCEGUI
    from PyCEGUI import Version__ as _PyCEGUIVersion
    PyCEGUI = _PyCEGUIVersion
    
except:
    # all of the other versions are just optional, what we always need and will always get
    # is the CEED version
    pass

