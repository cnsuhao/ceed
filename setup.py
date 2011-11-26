#!/usr/bin/env python
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

import os
from distutils.core import setup
from ceed import version

def get_packages():
    """Returns the whole list of ceed packages"""
    
    # Distutils requires us to list all packages, this is very tedious and prone
    # to errors. While I believe I should know which packages ceed has at all times
    # I also believe that saving work on my part is a "good thing".
    
    ret = ["ceed"]
    
    for dirpath, dirs, files in os.walk("ceed"):
        if "__init__.py" in files:
            ret.append(dirpath.replace(os.path.sep, "."))
            
    return ret    

setup(
    name = "CEED",
    version = version.CEED,
    description = "The CEGUI Unified Editor",
    author = "Martin Preisler and others (see AUTHORS)",
    author_email = "preisler.m@gmail.com",
    url = "http://www.cegui.org.uk/",
    packages = get_packages(),
    scripts = ["bin/ceed-gui", "bin/ceed-mic", "bin/ceed-migrate"]
)
