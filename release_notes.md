*************************************
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

*************************************
# Release Notes for OpenMDAO-XDSM 0.3

March 23, 2020

## Backwards Incompatible API Changes:

- None

## Backwards Incompatible NON-API Changes:

- pyxdsm is now on pypi, added as a dependency (instead of being optional), since now it is easy to install it.

## New Features:

- Updated docs.


## Bug Fixes:
- None

*************************************
# Release Notes for OpenMDAO-XDSM 0.4

March 27, 2020

## Backwards Incompatible API Changes:

- None

## Backwards Incompatible NON-API Changes:

- pyxdsm tests are not skipped, and pyxdsm is always tries to be imported. This can only break your code, if pyxdsm 
is not installed.

## New Features:

- None

## Bug Fixes:
- None