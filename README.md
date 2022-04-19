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
*Once things are somewhat more set up, this section contains how to get everything together and
setting up the environment. This should contain all the steps required for a new Collaborator
to get simulations and analyses running.*
