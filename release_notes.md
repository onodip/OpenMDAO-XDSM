*************************************
# Release Notes for OpenMDAO-XDSM 1.2

Feb 10, 2024

## Backwards Incompatible API Changes:

- None

## Backwards Incompatible NON-API Changes:

- added packaging to the dependencies

## New Features:

- None

## Bug Fixes:

- None

*************************************
# Release Notes for OpenMDAO-XDSM 1.1

Feb 9, 2024

## Backwards Incompatible API Changes:

- None

## Backwards Incompatible NON-API Changes:

- None

## New Features:

- Python 3.12 compatibility
- The settings in the sellar_xdsmjs.py example were updated to show a cleare diagram. 

## Bug Fixes:

- None


*************************************
# Release Notes for OpenMDAO-XDSM 1.0

May 16, 2023

## Backwards Incompatible API Changes:

- None

## Backwards Incompatible NON-API Changes:

- The omxdsm package was restructured, and some functions were moved into new files.

## New Features:

- Short class names (class names without module path), by passing class_names=short

## Bug Fixes:
- Fixed duplicate AutoIndepVarComp, when newer OpenMDAO versions were used.

*************************************
# Release Notes for OpenMDAO-XDSM 0.8

May 9, 2023

## Backwards Incompatible API Changes:

- None

## Backwards Incompatible NON-API Changes:

- None

## New Features:

- Compatibility with OpenMDAO 3.26 and beyond.

## Bug Fixes:
- Sellar example updates. In the current version include_indepvarcomps=False, class_names=False 
    options need to be used to create PDFs. To be fixed in a future release.

*************************************
# Release Notes for OpenMDAO-XDSM 0.7

January 27, 2023

## Backwards Incompatible API Changes:

- None

## Backwards Incompatible NON-API Changes:

- None

## New Features:

- Compatibility with OpenMDAO 3.21 and beyond.

## Bug Fixes:
- None

*************************************
# Release Notes for OpenMDAO-XDSM 0.6

July 31, 2020

## Backwards Incompatible API Changes:

- None

## Backwards Incompatible NON-API Changes:

- None

## New Features:

- Automatic IndepVarComps (new in OpenMDAO 3.2 - POEM_015) are supported.

## Bug Fixes:
- Models with Automatic IndepVarComps failed, which is now fixed.

*************************************
# Release Notes for OpenMDAO-XDSM 0.5

April 25, 2020

## Backwards Incompatible API Changes:

- None

## Backwards Incompatible NON-API Changes:

- The xdsmjs source code was removed.
- The xdsmjs Python package (https://pypi.org/project/xdsmjs/) was added to the dependencies.

## New Features:

- None

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
# Release Notes for OpenMDAO-XDSM 0.2

March 14, 2020

## Backwards Incompatible API Changes:

- None

## Backwards Incompatible NON-API Changes:

- Dependencies of the `six` package were removed. That means, that OpenMDAO-XDSM will be compatible only with 
    Python 3 (OpenMDAO 3 also dropped the Python 2 compatibility) 

## New Features:

- New option `include_inepvarcomps`. If it is false, the `IndepVarComp` instances of the model do not show up as 
    subsystems on the diagram, instead they are converted to a design variable or external input, which are connected
    to the target system(s) of the `IndepVarComp`. This simplifies the XDSM, without the loss of much information.

## Bug Fixes:
- None
