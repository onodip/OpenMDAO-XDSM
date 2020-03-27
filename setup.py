from setuptools import setup

__version__ = "0.4"
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
        "Operating System :: OS Independent",
        'Topic :: Scientific/Engineering',
        'Programming Language :: Python',
    ],
    install_requires=[
        'openmdao',  # 3.0.0-dev or above
        'numpy',
        'pyxdsm',
    ],
    extras_require={
        'tex': [
            'pytexit',
        ]
    },
    packages=[
        'omxdsm',
    ],
    entry_points={
        'openmdao_command': [
            'xdsm=omxdsm.cmd:_xdsm_setup'
        ],
    },
    include_package_data=True,
)