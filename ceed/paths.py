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
This module contains means to get various CEED related paths in various
environments.
"""

import os

"""Whether the application is frozen using cx_Freeze"""
frozen = False

from ceed import fake
"""What's the absolute path to the package directory"""
package_dir = os.path.dirname(os.path.abspath(fake.__file__))

if package_dir.endswith(os.path.join("library.zip", "ceed")):
    frozen = True
    package_dir = os.path.dirname(package_dir)

"""What's the absolute path to the data directory"""
data_dir = ""
"""Potential system data dir, we check it's existence and set
data_dir as system_data_dir if it exists
"""
system_data_dir = "/usr/share/ceed"
system_data_dir_exists = False
try:
    if os.path.exists(system_data_dir):
        data_dir = system_data_dir
        system_data_dir_exists = True
except:
    pass

if not system_data_dir_exists:
    data_dir = os.path.join(os.path.dirname(package_dir), "data")
    
"""What's the absolute path to the ui directory"""
ui_dir = os.path.join(package_dir, "ui")

# if one of these assertions fail your installation is not valid!
if not frozen:
    # these two checks will always fail in a frozen instance
    assert(os.path.exists(package_dir))
    assert(os.path.exists(ui_dir))
    
assert(os.path.exists(data_dir))
