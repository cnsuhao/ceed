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

def getPackageDir():
    import fake

    dir_ = os.path.dirname(os.path.abspath(fake.__file__))
    if dir_.endswith("library.zip"):
        # if this is a frozen copy, we have to strip library.zip
        dir_ = os.path.dirname(dir_)

    return dir_

def getDataDir():
    return os.path.join(os.path.dirname(getPackageDir()), "data")

def getUiDir():
    return os.path.join(getPackageDir(), "ui")

def fixCwd():
    """Sets CWD as the data directory in applications install directory.

    This is necessary when starting the app via shortcuts.
    """
    os.chdir(os.path.join(os.path.dirname(getPackageDir()), "data"))
