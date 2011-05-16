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

# MetaImageset compiler command line tool

from PySide.QtGui import QApplication

import argparse
import metaimageset

from xml.etree import ElementTree

def main():
    # we have to construct Qt application, otherwise all the pixmap functionality won't work
    QApplication([])
    
    parser = argparse.ArgumentParser(description = "Compile given meta imageset")
    
    parser.add_argument("--sizeIncrement", metavar = "X", type = int, required = False, default = 5, help = "Number of pixels the size is increased as a step in the size determination.")
    parser.add_argument("input", metavar = "INPUT_FILE", type = argparse.FileType("r"), help = "Input file to be processed.")
    
    args = parser.parse_args()
    
    metaImageset = metaimageset.MetaImageset(args.input.name)

    data = args.input.read()
    element = ElementTree.fromstring(data)
    metaImageset.loadFromElement(element)
    
    compiler = metaimageset.compiler.CompilerInstance(metaImageset)
    compiler.sizeIncrement = args.sizeIncrement
    compiler.compile()

    print("")
    print("Performed compilation of '%s'..." % (args.input.name))

if __name__ == "__main__":
    main()
