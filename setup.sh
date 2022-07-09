#!/bin/bash
usage() {
   echo "setup.sh [-aibeg]"
   echo " -i   initialise git submodules if not yet initialised"
   echo " -b   build the available PIONEER software"
   echo " -e   generate setenv.sh to set environment"
   echo " -g   build the test_output.gdml geometry file"
   echo " -a   all of the above"
}

if [ $# -eq 0 ]; then
   DO_INIT=TRUE
   DO_BUILD=TRUE
   DO_ENV=TRUE
   DO_GEOM=TRUE
fi

while getopts "aibeg" arg; do
   case $arg in
      a)
         DO_INIT=TRUE
         DO_BUILD=TRUE
         DO_GEOM=TRUE
         DO_ENV=TRUE
         ;;
      i)
         DO_INIT=TRUE
         ;;
      b)
         DO_BUILD=TRUE
         ;;
      e)
         DO_ENV=TRUE
         ;;
      g)
         DO_GEOM=TRUE
         ;;
      h | *)
         usage
         exit 1
         ;;
   esac
done

# Get directory of the script, i.e. PIONEERSYS
export PIONEERSYS=$(readlink -f $0 | sed 's/\/setup.sh//')

owd=$(pwd)
cd $PIONEERSYS
exec &> >(tee $PIONEERSYS/setup.log)

echo "PIONEER data located in $PIONEERSYS"


if [ $DO_INIT ]; then
   # Currently, initiate all submodules for the sake of simplicity.
   # Later, this should be more selective.
   # To initialise only a specific submodule, its name can be appended
   # to the git command below.
   
   echo Initialising all submodules
   PIONEER_SUBMOD=$(git submodule foreach | sed s/Entering// | sed s/\'//g)
   PIONEER_SUBMOD_AVAILABLE=$(git submodule status | awk '{print $2}')
   
   for SUBMOD in $PIONEER_SUBMOD_AVAILABLE; do
      if [[ $PIONEER_SUBMOD == *$SUBMOD* ]]; then
         echo $SUBMOD already initialised
      else
         echo Initialising $SUBMOD
         git submodule update --init --recursive $SUBMOD
      fi
   done
fi

# Print available submodules
PIONEER_SUBMOD=$(git submodule foreach | sed s/Entering// | sed s/\'//g)
echo "Initialised Submodules: " ${PIONEER_SUBMOD}
echo "Available Submodules:   " $(git submodule status | awk '{print $2}')


if [ $DO_BUILD ]; then
   # Building the simulation
   if [ "$PIONEER_SUBMOD" ]; then
      echo building PIONEER software
      
      if [[ ! $PIONEER_SUBMOD == *shared* ]]; then
         CMAKE_FLAGS="$CMAKE_FLAGS -DBUILD_SHARED=FALSE"
      fi
      if [[ ! $PIONEER_SUBMOD == *MonteCarlo* ]]; then
         CMAKE_FLAGS="$CMAKE_FLAGS -DBUILD_MC=FALSE"
      fi
      if [ $(uname) == Darwin ]; then
         # Compiling on MacOS
         CMAKE_FLAGS="$CMAKE_FLAGS -DCMAKE_OSX_DEPLOYMENT_TARGET=$(sw_vers -productVersion)"
         MAKE_FLAGS="$MAKE_FLAGS -j$(sysctl -n hw.physicalcpu)"
      else
         # Compiling on Linux
         MAKE_FLAGS="$MAKE_FLAGS -j$(nproc)"
      fi
      
      [ -d install ] || mkdir install
      [ -d build ] || mkdir build
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
   else
      echo No Submodules initialised. Nothing to build.
   fi
   cd $PIONEERSYS
fi

if [ $DO_GEOM ]; then
   # Build test_output.gdml, used by the example.mac macro for simulation
   if [[ $PIONEER_SUBMOD == *MonteCarlo* ]]; then
      # We have the MonteCarlo Submodule initialised
      if [ ! -f MonteCarlo/geometry/generator/test_output.gdml ]; then
         # build_geometry.py depends on PIMCSYS. Export it here.
         export PIMCSYS=${PIONEERSYS}/MonteCarlo
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
         cd $PIONEERSYS
      fi
   else
      echo Cant build Geometry file without MonteCarlo submodule.
   fi
fi

if [ $DO_ENV ]; then
   # write setenv.sh
   {
      echo "export PIONEERSYS=$PIONEERSYS"
      if [[ $PIONEER_SUBMOD == *MonteCarlo* ]]; then
         echo 'export PIMCSYS=${PIONEERSYS}/MonteCarlo'
      fi
      echo 'export PATH=${PATH}:${PIONEERSYS}/install/bin'
      if [ $(uname) == Darwin ]; then
         echo 'export DYLD_LIBRARY_PATH=${DYLD_LIBRARY_PATH}:${PIONEERSYS}/install/lib'
      else
         echo 'export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${PIONEERSYS}/install/lib'
      fi
   } > setenv.sh
   
   echo setenv.sh written.
   echo you can source this file to set up the environment required for PIONEER.
   echo To do this automatically, you can add this line to your shell config file
   echo
   echo source $PIONEERSYS/setenv.sh
   echo
fi
cd $owd
