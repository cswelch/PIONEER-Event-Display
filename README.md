# PIONEER Main Repository

## Overview
This is the main repository that contains all relevant subprojects for simulations and analyses required by the
PIONEER experiment. It is used to assert that the various parts of the code share a common ground and will
link against the same data structures.

## Subprojects

### shared
This repository contains shared libraries required by more than one of the other parts. Currently, it
consists only of the root dictionaries required to read/write the ROOT output files.

### MonteCarlo
**Requires: shared**

This contains the full Geant4 based simulation of the PIONEER experiment, including geometry generation
(subfolder geometry). Please consult the README located in that repository for further details.

## Getting Started
*This section should contain all information a new collaborator needs to get started, from setting
up the environment to running simple simulations and analyses. This is currently under construction.
Please report any issues you run into to Patrick Schwendimann [schwenpa@uw.edu](mailto:schwenpa@uw.edu).*

### Using Singularity
*to be written*

### Building the Simulation from Scratch

If you are using a container, skip this section.

**Prerequisites**

You are required to install the following dependencies Geant4 V4.11.00, ROOT V6.27/01 and XercesC 3.2.3 (newer versions might work as well) to compile and run the simulation as well as CMake to build the binaries. It is up to your taste if your prefer a cmake version with graphical user interface (e.g. ccmake). Additionaly, you will need a recent version of python to build the geometries.

To install geant yourself (linux), you can complete the following steps:
```
mdkir geant4; cd geant4
wget http://cern.ch/geant4-data/releases/geant4-v11.0.0.tar.gz
tar -zxvf geant4-v11.0.0.tar.gz
mkdir build; mkdir install
cd build
cmake -DGEANT4_INSTALL_DATA=ON \
      -DGEANT4_USE_GDML=ON \
      -DGEANT4_USE_PYTHON=ON \
      -DGEANT4_USE_OPENGL_X11=ON \
      -DBUILD_STATIC_LIBS=ON \
      -DCMAKE_INSTALL_PREFIX=../install \
      ../geant4-v11.0.0
make -jN
make install
```

You may need to specify the version of `g++` in your cmake command if you encounter a problem, like so:
```
-DCMAKE_CXX_COMPILER=/share/apps/gcc-9.1.0/bin/g++ -DCMAKE_CC_COMPILER=/share/apps/gcc-9.1.0/bin/gcc \
```

You may also need to speficy where your installation of `Xerces` lives, like:
```
-DXercesC_INCLUDE_DIR=/usr/local/include/ -DXercesC_LIBRARY=/usr/local/lib/libxerces-c-3.2.so  -DXercesC_VERSION=3.2.3 \
```

Optionally, to enable a non-root data output format (such as HDF5), you may also include the following option:

```
-DGEANT4_USE_HDF5=ON \
```

In addition to the data installed during the geant4 installation, you might require the additional file for the Low Energy Nuclear Data
and set up the corresponding path. It is linked from the official [Geant4 download site](https://geant4.web.cern.ch/support/download).
Save this file with your other data files. You will need to set up the environment variabe `G4LENDDATA` manually. Please see below.

For more detailed instructions, see the geant4 [setup guide](https://geant4-userdoc.web.cern.ch/UsersGuides/InstallationGuide/BackupVersions/V10.6c/html/installguide.html). 

To install ROOT, follow the steps documented in the [root installation guide]{https://root.cern/install/}. If you want to build root from source, there are the steps to follow:
```
mkdir root
cd root
git clone --branch latest-stable https://github.com/root-project/root.git root_src
mkdir root_build root_install
cd root_build
cmake -DCMAKE_INSTALL_PREFIX=../root_install ../root_src
make install
```
Instead of invoking `cmake` you most likely want to invoke `ccmake` or whatever graphical interface you are using and assert all flags are set properly.

**Cloning the Repository**

While it is possible to clone dedicated projects on its own, it is recommended to clone them all at once by using one of the following
```
# SSH
git clone --recurse-submodules git@github.com:PIONEER-Experiment/main.git PIONEER

# HTTPS
git clone --recurse-submodules https://github.com/PIONEER-Experiment/main.git PIONEER
```
While both options work, the SSH version requires that you have added an SSH-key to your github account (one time effort) while the
HTTPS version requires authentication each time you interface with the remote repository. Personally, I am in favour of the SSH-method.

*For Developers: Please note that all submodules will be in a detached head state as the main repository refers to commits rather than branches.
before you start developing new features, it is highly recommended to check out the current develop (or main) branch and create your own branch
based on this, e.g.*
```
cd MonteCarlo
git checkout develop
git pull
git checkout -b feature/myFeature
```

**Preparing the Environment**

Use your favourite editor to add the following lines to your `.bashrc` if you are using bash.

```
# source root
if [ -f PATH/TO/root/root_install/bin/thisroot.sh ]; then
   . PATH/TO/root/root_install/bin/thisroot.sh
else
   echo "ROOT not found"
fi

# source geant4
if [ -f PATH/TO/geant4/install/bin/geant4.sh ]; then
   . PATH/TO/geant4/install/bin/geant4.sh
   export G4LENDDATA=PATH/TO/geant4/data/LEND_GND1.3_ENDF.BVII.1
else
   echo "Geant4 not found"
fi

#PIONEER
# Let the system know where to find the simulation
export PIONEERSYS='PATH/TO/YOUR/PIONEER/FOLDER'

# Let the system know where to find the libraries. This causes Root to find the dictionaries automatically.
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${PIONEERSYS}/install/lib

# This allows you to run the simulation from wherever you want, allowing a working directory that is
# independent from the git repository.
export PATH=${PATH}:${PIONEERSYS}/install/bin
```
This example is written for bash type consoles in a Linux environment. Please adapt it to your local setting.
For a macos, you have to replace `LD_LIBRARY_PATH` with `DYLD_LIBRARY_PATH`.

If you are using `zsh` as your shell (e.g. newer macos by default), then the lines for Geant4 look a bit
different, as geant4.sh needs to be called from within the `bin` directory:
```
if [ -f PATH/TO/geant4/install/bin/geant4.sh ]; then
   owd=`pwd`
   cd PATH/TO/geant4/install/bin
   . ./geant4.sh
   export G4LENDDATA=PATH/TO/geant4/data/LEND_GND1.3_ENDF.BVII.1
   cd $owd
else
   echo "Geant4 not found"
fi
```

**Compiling the Simulation**

Once you have the prerequisites installed, you can compile and run the simulation:
```
cd path/to/PIONEER
mkdir build
mkdir install
cd build
cmake ..
make
make install
```
Again, depending on your installation and how your library paths are set you may need to manually specify the paths to `Xerces` or `g++`. 
The `make install` step will create the directories `bin` and `lib` inside the install directory. 
`lib` includes the root dictionary the simulation is linked against. 
`bin` contains the executables.

If the environment is set up such that `install/bin` is along your `PATH` and `install/lib` is along your `LD_LIBRARY_PATH` (`DYLD_LIBRARY_PATH` for macos), no further steps are required and you can run the simulation with
```
g4pienux path/to/macro.mac
```
The libraries should be linked such that they are accessible from any ROOT session.

If you have access to the CENPA-Rocks cluster, a tarred version of this installation (ROOT + Python + Geant) can be found at: `/data/g2/users/labounty/TargetSim_geant.tar.gz`

If you have problems getting set up, contact Josh LaBounty on [slack](https://app.slack.com/client/T01Q2T1MJ6L/D01PRM69NGH) or via [email](mailto:jjlab@uw.edu) or Patrick Schwendimann ([schwenpa@uw.edu](mailto:schwenpa@uw.edu)).
