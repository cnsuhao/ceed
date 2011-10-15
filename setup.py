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

# Allows freezing the executable (currently Windows specific code pretty much)

import platform

from ceed import version

VERSION = version.CEED
# TODO: these should branch depending on the platform
GUI_BASE_APP = "Console"
CONSOLE_BASE_APP = "Console"
EXECUTABLE_EXTENSION = ""

if platform.system() == "Windows":
    # Windows is being special again
    GUI_BASE_APP = "Win32GUI"
    EXECUTABLE_EXTENSION = ".exe"

from cx_Freeze import setup, Executable

buildOptions = dict(    
    packages =
    [
        "OpenGL",
        "OpenGL.GL",
        "OpenGL.GLU",
        "OpenGL.platform",
        "OpenGL.arrays.formathandler",
        
        "encodings.ascii",
        "encodings.utf_8",

        "PySide.QtNetwork",
        
        "PyCEGUI",
        "PyCEGUIOpenGLRenderer"
    ],
    
    include_files =
    [
        ["data", "data"]
    ]
)

setup(
    name = "CEED",
    version = VERSION,
    description = "CEGUI Unified Editor",
    options = dict(build_exe = buildOptions),
    executables = [
        # this starts the GUI editor main application
        Executable(
            "bin/ceed-gui.py",
            base = GUI_BASE_APP,
            targetName = "ceed-gui" + EXECUTABLE_EXTENSION,
            icon = "data/icons/application_icon.ico"
        ),
        
        # this starts the MetaImageset compiler
        Executable(
            "bin/ceed-mic.py",
            base = CONSOLE_BASE_APP,
            targetName = "ceed-mic" + EXECUTABLE_EXTENSION
        ),
        # this starts the Asset Migration tool
        Executable(
            "bin/ceed-migrate.py",
            base = CONSOLE_BASE_APP,
            targetName = "ceed-migrate" + EXECUTABLE_EXTENSION
        )
    ] 
)
