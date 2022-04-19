#----------------------------------------------------------------------------
# Setup the project
cmake_minimum_required(VERSION 3.0 FATAL_ERROR)
project(PIONEER_ALL)


# Set up global configuration
# ===========================

# Define default installation directory

if (CMAKE_INSTALL_PREFIX_INITIALIZED_TO_DEFAULT)
        set(CMAKE_INSTALL_PREFIX ${CMAKE_SOURCE_DIR}/install CACHE PATH "..." FORCE)
endif()

set(CMAKE_INSTALL_RPATH_USE_LINK_PATH TRUE)
set(CMAKE_INSTALL_RPATH ${CMAKE_INSTALL_PREFIX}/lib)


set(BUILD_SHARED TRUE CACHE BOOL "Build Shared Libraries")
set(BUILD_MC TRUE CACHE BOOL "Build Monte Carlo code")

# Add subprojects
# ===============

if (BUILD_SHARED) 
        add_subdirectory(shared)
endif()

if (BUILD_MC)
        if (NOT BUILD_SHARED)
                  message(SEND_ERROR "shared libraries are disabled but mandatory for MonteCarlo")
        else()
                  add_subdirectory(MonteCarlo)
        endif()
endif()
