find_package(PkgConfig)

PKG_CHECK_MODULES(PC_GR_EJFAT gnuradio-ejfat)

FIND_PATH(
    GR_EJFAT_INCLUDE_DIRS
    NAMES gnuradio/ejfat/api.h
    HINTS $ENV{EJFAT_DIR}/include
        ${PC_EJFAT_INCLUDEDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/include
          /usr/local/include
          /usr/include
)

FIND_LIBRARY(
    GR_EJFAT_LIBRARIES
    NAMES gnuradio-ejfat
    HINTS $ENV{EJFAT_DIR}/lib
        ${PC_EJFAT_LIBDIR}
    PATHS ${CMAKE_INSTALL_PREFIX}/lib
          ${CMAKE_INSTALL_PREFIX}/lib64
          /usr/local/lib
          /usr/local/lib64
          /usr/lib
          /usr/lib64
          )

include("${CMAKE_CURRENT_LIST_DIR}/gnuradio-ejfatTarget.cmake")

INCLUDE(FindPackageHandleStandardArgs)
FIND_PACKAGE_HANDLE_STANDARD_ARGS(GR_EJFAT DEFAULT_MSG GR_EJFAT_LIBRARIES GR_EJFAT_INCLUDE_DIRS)
MARK_AS_ADVANCED(GR_EJFAT_LIBRARIES GR_EJFAT_INCLUDE_DIRS)
