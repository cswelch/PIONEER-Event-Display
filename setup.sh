#!/bin/bash

# Get directory of the script, i.e. PIONEERSYS
export PIONEERSYS=$(readlink -f $0 | sed 's/\/setup.sh//')

owd=$(pwd)
cd $PIONEERSYS
exec &> >(tee $PIONEERSYS/setup.log)

echo "PIONEER data located in $PIONEERSYS"

# Currently, initiate all submodules for the sake of simplicity.
# Later, this should be more selective.
# To initialise only a specific submodule, its name can be appended
# to the git command below.

echo Initialising all submodules
git submodule update --init --recursive

# Print available submodules
PIONEER_SUBMOD=$(git submodule foreach | sed s/Entering// | sed s/\'//g)
echo "Initialised Submodules: " $PIONEER_SUBMOD
echo "Available Submodules:   " $(git submodule status | awk '{print $2}')

# Building the simulation
echo building PIONEER software

if [ $(uname) == Darwin ]; then
   # Compiling on MacOS
   CMAKE_FLAGS="$CMAKE_FLAGS -DCMAKE_OSX_DEPLOYMENT_TARGET=$(sw_vers -productVersion)"
   MAKE_FLAGS="$MAKE_FLAGS -j$(sysctl -n hw.physicalcpu)"
else
   # Compiling on Linux
   MAKE_FLAGS="$MAKE_FLAGS -j$(nproc)"
fi

mkdir install
mkdir build
cd build
echo
echo ______ CMAKE _______
echo cmake $CMAKE_FLAGS $PIONEERSYS
cmake $CMAKE_FLAGS $PIONEERSYS
cmake_exit=$?
echo --------------------
if [ ! $cmake_exit == 0 ]; then
   echo cmake failed with exit status $cmake_exit.
   echo check the error message for hints and make sure
   echo that you set up ROOT and Geant4 environment, i.e.
   echo sourced the appropriate setup scripts.
   exit 1
fi

echo
echo --- MAKE INSTALL ---
echo make install $MAKE_FLAGS
make install $MAKE_FLAGS
echo --------------------

cd $PIONEERSYS
# Build test_output.gdml, used by the example.mac macro for simulation
if [[ $PIONEER_SUBMOD == *MonteCarlo* ]]; then
   # We have the MonteCarlo Submodule initialised
   if [ ! -f MonteCarlo/geometry/generator/test_output.gdml ]; then
      cd MonteCarlo/geometry/generator
      echo building test_output.gdml
      if [[ $(python -V) == "Python 3."* ]]; then
         python build_geometry.py config_files/geometry_params.json >> geom.log 2>&1
      else
         python3 build_geometry.py config_files/geometry_params.json >> geom.log 2>&1
      fi
      if [ -f test_output.gdml ]; then
         echo "done" 
      else
         echo "failed"
      fi
   fi
fi

# write setenv.sh
cd $PIONEERSYS
echo "export PIONEERSYS=$PIONEERSYS" > setenv.sh
echo 'export PATH=${PATH}:${PIONEERSYS}/install/bin' >> setenv.sh
if [ $(uname) == Darwin ]; then
   echo 'export DYLD_LIBRARY_PATH=${DYLD_LIBRARY_PATH}:${PIONEERSYS}/install/lib' >> setenv.sh
else
   echo 'export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${PIONEERSYS}/install/lib' >> setenv.sh
fi

echo setenv.sh written.
echo you can source this file to set up the environment required for PIONEER.
echo To do this automatically, you can add this line to your shell config file
echo
echo source $PIONEERSYS/setenv.sh
echo
cd $owd
