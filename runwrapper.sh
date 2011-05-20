#!/bin/bash

# Sure the linker gurus wouldn't approve, but I use this to avoid having to mess
# with RPATH or having to install everything when I rebuild

# Obviously doesn't work on Windows ;-)

# relative to where you run the script from or absolute (probably a more robust solution)
CEGUI_BUILD_PATH="../cegui_mk2"

# Not needed with the new RPATH stuff in 0.8
#export LD_LIBRARY_PATH="$CEGUI_BUILD_PATH/build/cegui/src/:$CEGUI_BUILD_PATH/build/cegui/src/RendererModules/OpenGL:$LD_LIBRARY_PATH"

export PYTHONPATH="$CEGUI_BUILD_PATH/build/lib:$PYTHONPATH"

# fork a new shell with this PYTHONPATH to avoid polluting the environment
bash
