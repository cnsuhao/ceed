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
    import version.prerequisites

    if version.prerequisites.check():
        import sys
        import os

        import application

        # FIXME: This should be moved somewhere to be reusable, as well as getInstallDir
        def fixCwd():
            """Sets CWD as the applications install directory"""

            # this is necessary when starting the app via shortcuts

            def getInstallDir():
                import fake

                dir = os.path.dirname(os.path.abspath(fake.__file__))

                if dir.endswith("library.zip"):
                    # if this is a frozen copy, we have to strip library.zip
                    dir = os.path.dirname(dir)

                return dir

            os.chdir(getInstallDir())

        fixCwd()

        app = application.Application(sys.argv)
        sys.exit(app.exec_())

    else:
        print("Your environment doesn't meet critical prerequisites! Can't start!")

if __name__ == "__main__":
    main()
