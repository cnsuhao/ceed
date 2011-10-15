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
This module contains fixes for the host environment.
"""

import os

def getInstallDir():
    import fake

    dir = os.path.dirname(os.path.abspath(fake.__file__))
    if dir.endswith("library.zip"):
        # if this is a frozen copy, we have to strip library.zip
        dir = os.path.dirname(dir)

    return dir

def fixCwd():
    """Sets CWD as the applications install directory.

    This is necessary when starting the app via shortcuts.
    """
    os.chdir(getInstallDir())
