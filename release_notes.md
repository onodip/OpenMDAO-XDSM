**********************************
# Release Notes for OpenMDAO-XDSM 0.2

March 14, 2020

## Backwards Incompatible API Changes:

- None

## Backwards Incompatible NON-API Changes:

- Depencencies of the `six` package were removed. That means, that OpenMDAO-XDSM will be compatible only with 
    Python 3 (OpenMDAO 3 also dropped the Python 2 compatibility) 

## New Features:

- New option `include_inepvarcomps`. If it is false, the `IndepVarComp` instances of the model do not show up as 
    subsystems on the diagram, instead they are converted to a design variable or external input, which are connected
    to the target system(s) of the `IndepVarComp`. This simplifies the XDSM, without the loss of much information.


## Bug Fixes:
- None