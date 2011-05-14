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

import sys
import argparse

def main():
    parser = argparse.ArgumentParser(description = "Migrate given files using compatibility layers of the editor")
    
    parser.add_argument("category", type = str, help = "Which compatibility category to use ('imageset', 'layout').")
    parser.add_argument("--sourceType", type = str, default = "Auto", nargs = "?", help = "What is the source type of the data, if omitted, the type will be guessed")
    parser.add_argument("--targetType", type = str, default = "Native", nargs = "?", help = "What should the target type be. If omitted, editor's native type is used")
    
    parser.add_argument("input", metavar = "INPUT_FILE", type = argparse.FileType("r"), help = "Input file to be processed.")
    parser.add_argument("output", metavar = "OUTPUT_FILE", type = argparse.FileType("w"), help = "Output / target file path.")
    
    args = parser.parse_args()
    
    if args.category == "imageset":
        import compatibility.imageset as compat
        
    else:    
        print("Provided compatibility is not valid, such a compatibility module doesn't exist or can't be imported!")
        sys.exit(1)
    
    print "\nStarting migration!\n"    
    data = args.input.read()
    
    sourceType = args.sourceType if args.sourceType != "Auto" else compat.Manager.instance.guessType(data, args.input.name)
    targetType = args.targetType if args.targetType != "Native" else compat.EditorNativeType

    outputData = compat.Manager.instance.transform(sourceType, targetType, data)
    
    args.output.write(outputData)

    print "Performed migration from '%s' to '%s'.\ninput size: %i bytes\noutput size: %i bytes" % (sourceType, targetType, len(data), len(outputData))

if __name__ == "__main__":
    main()
