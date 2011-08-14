#!/bin/bash

# Sure the linker gurus wouldn't approve, but I use this to avoid having to mess
# with RPATH or having to install everything when I rebuild

# Obviously doesn't work on Windows ;-) But works OK on Linux and MacOSX

# relative to where you run the script from or absolute (probably a more robust solution)
CEGUI_BUILD_PATH="../cegui_mk2"

# Not needed with the new RPATH stuff in 0.8
#export LD_LIBRARY_PATH="$CEGUI_BUILD_PATH/build/cegui/src/:$CEGUI_BUILD_PATH/build/cegui/src/RendererModules/OpenGL:$LD_LIBRARY_PATH"

export PYTHONPATH="$CEGUI_BUILD_PATH/build/lib:$PYTHONPATH"

# on MacOSX we have to add Qt frameworks to the framework path
if [[ "`uname`" == 'Darwin' ]]; then
    # FIXME: This is hardcoded for Qt 4.7.3 :-(
    export DYLD_FRAMEWORK_PATH="$HOME/QtSDK/Desktop/Qt/473/gcc/lib/:$DYLD_FRAMEWORK_PATH"
fi

# fork a new shell to avoid polluting the environment
bash
