################################################################################
#   CEED - A unified CEGUI editor
#   Copyright (C) 2011 Martin Preisler <preisler.m@gmail.com>
#
#   Taken with very minor changes from CELE2 by Paul D Turner
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
from pysideuic import compileUi

# written by Paul D Turner for CELayoutEditorII
def compileUIFiles(ui_dir):
    for name in os.listdir(ui_dir):
        ui_name = os.path.join(ui_dir, name)
        if os.path.isfile(ui_name):
            if name.endswith(".ui"):
                outname = name[:-3] + ".py"
                outname = outname.lower()
                outfile = open(os.path.join(ui_dir, outname), "w")
                compileUi(ui_name, outfile)
                outfile.close()

def main():
    from ceed import paths
    
    compileUIFiles(paths.ui_dir)
    compileUIFiles(paths.ui_dir + "/editors")
    compileUIFiles(paths.ui_dir + "/editors/animation_list")
    compileUIFiles(paths.ui_dir + "/editors/imageset")
    compileUIFiles(paths.ui_dir + "/editors/layout")
    compileUIFiles(paths.ui_dir + "/widgets")
    
if __name__ == "__main__":
    main()
