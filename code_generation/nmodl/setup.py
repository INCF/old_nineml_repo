#!/usr/bin/env python

from distribute_setup import use_setuptools
use_setuptools()
from setuptools import setup

setup(
    name = "9ml2nmodl",
    version = "0.1.0",
    packages = ['nineml2nmodl', 'nineml2nmodl.test'],
    #package_data = {'nineml2nmodl': ['nmodl_template.jinja']},
    scripts = ['bin/9ml2nmodl'],
    author = "Andrew P. Davison, Michael Hull", # add your name here if you contribute to the code
    author_email = "nineml-users@incf.org",
    description = "A tool for generating NMODL mechanisms for the NEURON simulator (http://www.neuron.yale.edu) from model descriptions in NineML (http://www.nineml.org/)",
    long_description = open("README").read(),
    license = "BSD 3 License",
    keywords = "computational neuroscience modeling interoperability XML NEURON NMODL",
    url = "http://nineml.incf.org",
    classifiers = ['Development Status :: 2 - Pre-Alpha',
                   'Environment :: Console',
                   'Intended Audience :: Science/Research',
                   'License :: Other/Proprietary License',
                   'Natural Language :: English',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python :: 2',
                   'Topic :: Scientific/Engineering'],
    install_requires = ['nineml', 'Cheetah'],
    tests_require = ['matplotlib']
)

