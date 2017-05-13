cmake_minimum_required(VERSION 2.6)

project("CEED")
set(CEED_VERSION_MAJOR "0")
set(CEED_VERSION_MINOR "8")
set(CEED_VERSION_PATCH "1")
set(CEED_VERSION "${CEED_VERSION_MAJOR}.${CEED_VERSION_MINOR}.${CEED_VERSION_PATCH}")
set(CMAKE_MODULE_PATH ${CMAKE_MODULE_PATH} "${CMAKE_SOURCE_DIR}/cmake/")

include(GNUInstallDirs)

find_package(CEGUI REQUIRED)
find_package(Qt4 REQUIRED QtCore QtGui QtXmlPatterns)

add_subdirectory("ceed")

install(FILES "${CMAKE_SOURCE_DIR}/LICENSE"
    DESTINATION ${CMAKE_INSTALL_DOCDIR})

install(FILES "${CMAKE_SOURCE_DIR}/README.md"
    DESTINATION ${CMAKE_INSTALL_DOCDIR})

# only CPack should follow
set(CPACK_CMAKE_GENERATOR "Unix Makefiles")
set(CPACK_SOURCE_GENERATOR "TBZ2")
set(CPACK_SOURCE_PACKAGE_FILE_NAME "ceed-${CEED_VERSION}" CACHE INTERNAL "tarball basename")
set(CPACK_SOURCE_IGNORE_FILES
"\\\\.hg.*"

"build/"
"~$"

"\\\\.settings/"
"\\\\.project"
"\\\\.cproject"

"\\\\CMakeLists.txt.user"
)
include(CPack)
