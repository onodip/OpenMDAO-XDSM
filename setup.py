from setuptools import setup

__version__ = "0.0"
__author__ = 'Peter Onodi'

setup(
    name='omxdsm',
    version=__version__,
    description="XDSM viewer plugin for OpenMDAO",
    keywords='openmdao_command openmdao xdsm optimization multidisciplinary multi-disciplinary',
    author=__author__,
    classifiers=[
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX :: Linux',
        'Operating System :: Microsoft :: Windows',
        'Topic :: Scientific/Engineering',
        'Programming Language :: Python',
    ],
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