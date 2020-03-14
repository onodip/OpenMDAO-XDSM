# OpenMDAO-XDSM
[XDSM][0] viewer plugin for [OpenMDAO][5].

More detailed documentation can be found in the `omxdsm/docs` folder.

## Installation

The package can be installed from the [Github repository][1]

Install the basic package using pip:

    pip install omxdsm@https://github.com/onodip/OpenMDAO-XDSM/tarball/master

With the basic installation XDSM diagrams can be created only in HTML format using 
[XDSMjs][2].

As an alternative, download or clone the repository, go to the directory and install the full package:

    pip install -e .[tex]
    
This also installs the [pyXDSM][3] package, and enables the creation of XDSM diagrams in TeX format.

## Testing
Run the tests in `omxdsm/tests/test_xdsm_viewer.py`
For development, setting the variables `DEBUG=True` and `SHOW=True` in this file will save the outputs of test 
functions and open them in the default browser and PDF viewer.

## OpenMDAO compatibility
This package was created after the introduction of the OpenMDAO [plugin system][4]. In OpenMDAO versions between 
2.7 and 3.0 it was part of the OpenMDAO package. The package is compatible  OpenMDAO versions above 3.0. 

[0]: http://mdolab.engin.umich.edu/content/xdsm-overview
[1]: https://github.com/onodip/OpenMDAO-XDSM
[2]: https://github.com/OneraHub/XDSMjs
[3]: https://github.com/mdolab/pyXDSM
[4]: http://openmdao.org/twodocs/versions/3.0.0/features/experimental/plugins.html
[5]: https://openmdao.org/