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

VERSION = "0.1"
# TODO: these should branch depending on the platform
GUI_BASE_APP = "Win32GUI"
CONSOLE_BASE_APP = "Console"
EXECUTABLE_EXTENSION = ".exe"

from cx_Freeze import setup, Executable

buildOptions = dict(    
    packages =
    [
        "OpenGL",
        "OpenGL.platform",
        "OpenGL.arrays.formathandler"
    ],
    
    include_files =
    [
        "icons",
        "images",
        "ui", # FIXME: because we always rebuild those upon starting
        "data"
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
            "entry.py",
            base = GUI_BASE_APP,
            targetName = "CEED" + EXECUTABLE_EXTENSION,
            icon = "icons/application_icon.ico"
        ),
        
        # this starts the MetaImageset compiler
        #Executable(
        #    "mic/entry.py",
        #    base = CONSOLE_BASE_APP,
        #    targetName = "mic" + EXECUTABLE_EXTENSION,
        #    icon = "icons/metaimageset_compiler.ico"
        #),
        # this starts the Asset Migration tool
        #Executable(
        #    "compatibility/entry.py",
        #    base = CONSOLE_BASE_APP,
        #    targetName = "migrate" + EXECUTABLE_EXTENSION,
        #    icon = "icons/migrate_icon.ico"
        #)
    ] 
)
