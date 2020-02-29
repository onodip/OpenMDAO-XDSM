from setuptools import setup

__version__ = "0.0"

setup(
    name='omxdsm',
    version=__version__,
    description="XDSM viewer plugin for OpenMDAO",
    keywords='openmdao_command openmdao xdsm optimization multidisciplinary multi-disciplinary',
    author='Peter Onodi',
    author_email='p.onodi@gmail.com',
    install_requires=[
        'openmdao>=2.10',
    ],
    packages=[
        'omxdsm',
    ],
    entry_points={
        'openmdao_command': [
            'xdsm_plugin=omxdsm.cmd:_xdsm_setup'
        ]
    },
)