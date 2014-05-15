@echo off

rem parent of this file
set DIR_PARENT_OF_FILE=%~dp0

rem relative directory where the "ceed" package is located
set CEED_PACKAGE_PATH=%DIR_PARENT_OF_FILE%/../

rem relative path to where you run the script from or absolute (probably a more robust solution)
set CEGUI_BUILD_PATH=%CEED_PACKAGE_PATH%/../cegui-v0-8


set PATH=%CEGUI_BUILD_PATH%/build/bin;%PATH%

set PYTHONPATH=%CEGUI_BUILD_PATH%/build/bin;%CEED_PACKAGE_PATH%;%PYTHONPATH%

start cmd.exe

python ceed-gui