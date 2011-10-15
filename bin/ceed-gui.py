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

def main():
    from ceed.version import prerequisites

    if prerequisites.check():
        import sys
        import os

        from ceed import application
        from ceed import paths

        # cwd has to be data dir for Qt to load the icons correctly
        os.chdir(paths.data_dir)

        app = application.Application(sys.argv)
        sys.exit(app.exec_())

    else:
        print("Your environment doesn't meet critical prerequisites! Can't start!")

if __name__ == "__main__":
    main()
